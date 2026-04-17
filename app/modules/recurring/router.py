from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.accounts.service import get_account_by_id
from app.modules.category.service import get_category_by_id
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.recurring.dependencies import get_owned_recurring
from app.modules.recurring.models import RecurringTransaction
from app.modules.recurring.schemas import (
    RecurringCreate,
    RecurringResponse,
    RecurringSummary,
    RecurringUpdate,
)
from app.modules.recurring.service import (
    create_recurring,
    deactivate_recurring,
    execute_single_recurring,
    get_recurring_summary,
    get_recurring_by_user,
    update_recurring,
)

router = APIRouter(prefix="/v1/recurring", tags=["Recurring Transactions"])


@router.post(
    "",
    response_model=RecurringResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    data: RecurringCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await get_account_by_id(db, data.account_id)
    if account is None or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    if data.category_id is not None:
        category = await get_category_by_id(db, data.category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        if category.user_id not in (None, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        if category.type.value != data.type.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category type '{category.type.value}' "
                f"does not match transaction type "
                f"'{data.type.value}'",
            )

    recurring = await create_recurring(db, current_user.id, data)
    return recurring


@router.get("", response_model=list[RecurringResponse])
async def list_recurring(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    recurring_status: Literal["active", "inactive", "all"] = Query(
        default="active",
        alias="status",
        description="Filter recurring templates by status",
    ),
):
    return await get_recurring_by_user(
        db,
        current_user.id,
        status=recurring_status,
    )


@router.get("/summary", response_model=RecurringSummary)
async def summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_recurring_summary(db, current_user.id)


@router.get("/{recurring_id}", response_model=RecurringResponse)
async def detail(
    recurring: RecurringTransaction = Depends(get_owned_recurring),
):
    return recurring


@router.put(
    "/{recurring_id}",
    response_model=RecurringResponse,
)
async def update(
    data: RecurringUpdate,
    recurring: RecurringTransaction = Depends(get_owned_recurring),
    db: AsyncSession = Depends(get_db),
):
    if data.category_id is not None:
        category = await get_category_by_id(db, data.category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        if category.user_id not in (None, recurring.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        if category.type.value != recurring.type.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category type '{category.type.value}' "
                f"does not match transaction type "
                f"'{recurring.type.value}'",
            )

    try:
        updated = await update_recurring(db, recurring, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return updated


@router.post(
    "/{recurring_id}/execute",
    status_code=status.HTTP_200_OK,
)
async def execute(
    recurring: RecurringTransaction = Depends(get_owned_recurring),
    db: AsyncSession = Depends(get_db),
):
    try:
        was_executed = await execute_single_recurring(db, recurring)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not was_executed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot execute: template is inactive, "
            "already ran today, or has reached its limit",
        )

    await db.commit()
    await db.refresh(recurring)

    return {
        "message": "Recurring transaction executed successfully",
        "next_due_date": str(recurring.next_due_date),
        "occurrence_count": recurring.occurrence_count,
    }
    
    
@router.delete(
    "/{recurring_id}",
    status_code=status.HTTP_200_OK,
)
async def delete(
    recurring: RecurringTransaction = Depends(get_owned_recurring),
    db: AsyncSession = Depends(get_db),
):
    await deactivate_recurring(db, recurring)
    return {"message": "Recurring transaction deactivated"}
