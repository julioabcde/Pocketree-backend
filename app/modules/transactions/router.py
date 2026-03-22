from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.accounts.service import get_account_by_id
from app.modules.category.service import get_category_by_id
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.transactions.dependencies import get_owned_transaction
from app.modules.transactions.models import Transaction, TransactionType
from app.modules.transactions.schemas import (
    TransactionCreate,
    TransactionResponse,
    TransactionSummary,
    TransactionTransfer,
    TransactionUpdate,
    TransferResponse,
)
from app.modules.transactions.service import (
    create_transaction,
    create_transfer,
    get_transaction_by_id,
    get_transactions_by_user,
    get_transaction_summary,
    soft_delete_transaction,
    update_transaction,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    data: TransactionCreate,
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
                f"does not match transaction type '{data.type.value}'",
            )

    transaction = await create_transaction(db, current_user.id, data)
    return transaction


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    account_id: int | None = Query(
        default=None,
        description="Filter by account",
    ),
    category_id: int | None = Query(
        default=None,
        description="Filter by category",
    ),
    type: TransactionType | None = Query(
        default=None,
        description="Filter by income or expense",
    ),
    start_date: date | None = Query(
        default=None,
        description="Transactions on or after this date (YYYY-MM-DD)",
    ),
    end_date: date | None = Query(
        default=None,
        description="Transactions on or before this date (YYYY-MM-DD)",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Results per page (1-100)",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of results to skip",
    ),
):
    transactions = await get_transactions_by_user(
        db,
        current_user.id,
        account_id=account_id,
        category_id=category_id,
        transaction_type=type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return transactions


@router.get("/summary", response_model=TransactionSummary)
async def summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    account_id: int | None = Query(
        default=None,
        description="Summary for specific account",
    ),
    category_id: int | None = Query(
        default=None,
        description="Summary for specific category",
    ),
    date_from: date | None = Query(
        default=None,
        description="Start date (YYYY-MM-DD)",
    ),
    date_to: date | None = Query(
        default=None,
        description="End date (YYYY-MM-DD)",
    ),
):
    result = await get_transaction_summary(
        db,
        current_user.id,
        account_id=account_id,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
    )
    return result


@router.post(
    "/transfer",
    response_model=TransferResponse,
    status_code=status.HTTP_201_CREATED,
)
async def transfer(
    data: TransactionTransfer,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from_account = await get_account_by_id(db, data.from_account_id)
    if from_account is None or from_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source account not found",
        )

    to_account = await get_account_by_id(db, data.to_account_id)
    if to_account is None or to_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination account not found",
        )

    try:
        from_txn, to_txn = await create_transfer(
            db,
            user_id=current_user.id,
            from_account_id=data.from_account_id,
            to_account_id=data.to_account_id,
            amount=data.amount,
            transfer_date=data.date,
            note=data.note,
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer failed. Please check your accounts.",
        )

    return TransferResponse(
        from_transaction=from_txn,
        to_transaction=to_txn,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def detail(
    transaction: Transaction = Depends(get_owned_transaction),
):
    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update(
    data: TransactionUpdate,
    transaction: Transaction = Depends(get_owned_transaction),
    db: AsyncSession = Depends(get_db),
):
    if transaction.is_transfer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Transfer transactions cannot be modified. "
            "Delete the transfer and create a new one.",
        )

    if data.category_id is not None:
        category = await get_category_by_id(db, data.category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        if category.user_id not in (None, transaction.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        if category.type.value != transaction.type.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category type '{category.type.value}' "
                f"does not match transaction type "
                f"'{transaction.type.value}'",
            )

    updated = await update_transaction(db, transaction, data)
    return updated


@router.delete("/{transaction_id}", status_code=status.HTTP_200_OK)
async def delete(
    transaction: Transaction = Depends(get_owned_transaction),
    db: AsyncSession = Depends(get_db),
):
    if transaction.is_transfer:
        # Load the paired transaction
        paired = await get_transaction_by_id(db, transaction.transfer_id)
        if paired is not None:
            await soft_delete_transaction(db, paired)

    await soft_delete_transaction(db, transaction)
    return {"message": "Transaction deleted successfully"}
