from decimal import Decimal
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accounts.models import Account, AccountType, ASSET_TYPES
from app.modules.accounts.schemas import AccountCreate, AccountUpdate

__all__ = [
    "create_default_account",
    "create_account",
    "get_account_by_id",
    "get_accounts_by_user",
    "get_account_summary",
    "update_account",
    "soft_delete_account",
    "check_duplicate_account",
]


async def create_default_account(db: AsyncSession, user_id: int) -> Account:
    account = Account(
        user_id=user_id,
        name="Cash",
        type=AccountType.cash,
        balance=Decimal("0.00"),
        initial_balance=Decimal("0.00"),
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def check_duplicate_account(
    db: AsyncSession,
    user_id: int,
    name: str,
    account_type: str,
    exclude_id: int | None = None,
) -> bool:
    query = select(Account).where(
        Account.user_id == user_id,
        func.lower(Account.name) == func.lower(name),
        Account.type == account_type,
        ~Account.is_deleted,
    )

    if exclude_id is not None:
        query = query.where(Account.id != exclude_id)

    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def create_account(
    db: AsyncSession, user_id: int, data: AccountCreate
) -> Account:
    account = Account(
        user_id=user_id,
        name=data.name,
        type=data.type,
        balance=data.initial_balance,
        initial_balance=data.initial_balance,
    )

    db.add(account)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account with name '{data.name}' already exists",
        )

    await db.refresh(account)
    return account


async def get_account_by_id(
    db: AsyncSession, account_id: int
) -> Account | None:
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            ~Account.is_deleted,
        )
    )
    return result.scalar_one_or_none()


async def get_accounts_by_user(
    db: AsyncSession, user_id: int
) -> list[Account]:
    result = await db.execute(
        select(Account)
        .where(
            Account.user_id == user_id,
            ~Account.is_deleted,
        )
        .order_by(Account.created_at.desc())
    )
    return list(result.scalars().all())


async def get_account_summary(db: AsyncSession, user_id: int) -> dict:
    result = await db.execute(
        select(
            Account.type,
            func.coalesce(func.sum(Account.balance), Decimal("0.00")),
        )
        .where(
            Account.user_id == user_id,
            ~Account.is_deleted,
        )
        .group_by(Account.type)
    )
    rows = result.all()

    total_assets = Decimal("0.00")
    total_liabilities = Decimal("0.00")

    for account_type, total in rows:
        if account_type in ASSET_TYPES:
            total_assets += total
        else:
            total_liabilities += total

    return {
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "net_worth": total_assets - total_liabilities,
        "accounts_count": sum(1 for _ in rows),
    }


async def update_account(
    db: AsyncSession, account: Account, data: AccountUpdate
) -> Account:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    await db.commit()
    await db.refresh(account)
    return account


async def soft_delete_account(db: AsyncSession, account: Account) -> Account:
    account.is_deleted = True
    account.deleted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(account)
    return account
