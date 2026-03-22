from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.accounts.dependencies import get_owned_account
from app.modules.accounts.models import Account
from app.modules.accounts.schemas import (
    AccountCreate,
    AccountResponse,
    AccountSummary,
    AccountUpdate,
)
from app.modules.accounts.service import (
    create_account,
    get_accounts_by_user,
    get_account_summary,
    soft_delete_account,
    update_account,
    check_duplicate_account,
)
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

router = APIRouter(prefix="/v1/accounts", tags=["Accounts"])


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_duplicate = await check_duplicate_account(
        db, current_user.id, data.name, data.type
    )
    if is_duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active account with the same name and type already exists.",
        )

    try:
        account = await create_account(db, current_user.id, data)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active account with the same name and type already exists.",
        )

    return account


@router.get(
    "",
    response_model=list[AccountResponse],
)
async def list_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    accounts = await get_accounts_by_user(db, current_user.id)
    return accounts


@router.get(
    "/summary",
    response_model=AccountSummary,
)
async def summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await get_account_summary(db, current_user.id)
    return result


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
)
async def detail(
    account: Account = Depends(get_owned_account),
):
    return account


@router.put(
    "/{account_id}",
    response_model=AccountResponse,
)
async def update(
    data: AccountUpdate,
    account: Account = Depends(get_owned_account),
    db: AsyncSession = Depends(get_db),
):
    final_name = data.name if data.name is not None else account.name
    final_type = data.type if data.type is not None else account.type

    name_changed = final_name != account.name
    type_changed = final_type != account.type

    if name_changed or type_changed:
        is_duplicate = await check_duplicate_account(
            db,
            account.user_id,
            final_name,
            final_type,
            exclude_id=account.id,
        )
        if is_duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active account with the same name and type already exists.",
            )

    try:
        updated = await update_account(db, account, data)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active account with the same name and type already exists.",
        )

    return updated


@router.delete(
    "/{account_id}",
)
async def delete(
    account: Account = Depends(get_owned_account),
    db: AsyncSession = Depends(get_db),
):
    await soft_delete_account(db, account)
    return {"message": "Account deleted successfully"}
