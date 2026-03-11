from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accounts.models import Account
from app.modules.accounts.schemas import AccountCreate, AccountUpdate

__all__ = [
    "create_account",
    "get_account_by_id",
    "get_accounts_by_user",
    "get_account_summary",
    "update_account",
    "soft_delete_account",
]


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
    await db.commit()
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
            func.coalesce(func.sum(Account.balance), Decimal("0.00")).label(
                "total_balance"
            ),
            func.count(Account.id),
        ).where(
            Account.user_id == user_id,
            ~Account.is_deleted,
        )
    )
    row = result.one()
    return {
        "total_balance": row[0],
        "accounts_count": row[1],
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
