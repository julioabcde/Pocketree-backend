from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accounts.models import Account
from app.modules.reports.service import invalidate_reports_cache
from app.modules.transactions.models import Transaction, TransactionType
from app.modules.transactions.schemas import (
    TransactionCreate,
    TransactionUpdate,
)

__all__ = [
    "create_transaction",
    "get_transaction_by_id",
    "get_transactions_by_user",
    "get_transaction_summary",
    "get_daily_summary",
    "update_transaction",
    "soft_delete_transaction",
    "create_transfer",
]


async def create_transaction(
    db: AsyncSession,
    user_id: int,
    data: TransactionCreate,
) -> Transaction:
    transaction = Transaction(
        user_id=user_id,
        account_id=data.account_id,
        category_id=data.category_id,
        type=data.type,
        amount=data.amount,
        date=data.date,
        note=data.note,
    )
    db.add(transaction)

    if data.type == TransactionType.income:
        balance_change = data.amount
    else:
        balance_change = -data.amount

    await db.execute(
        update(Account)
        .where(Account.id == data.account_id)
        .values(balance=Account.balance + balance_change)
    )

    await db.commit()
    await db.refresh(transaction)
    await invalidate_reports_cache(user_id)
    return transaction


async def get_transaction_by_id(
    db: AsyncSession,
    transaction_id: int,
) -> Transaction | None:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            ~Transaction.is_deleted,
        )
    )
    return result.scalar_one_or_none()


async def get_transactions_by_user(
    db: AsyncSession,
    user_id: int,
    account_id: int | None = None,
    category_id: int | None = None,
    transaction_type: TransactionType | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Transaction]:
    query = select(Transaction).where(
        Transaction.user_id == user_id,
        ~Transaction.is_deleted,
    )

    limit = min(limit, 100)

    if account_id is not None:
        query = query.where(Transaction.account_id == account_id)

    if category_id is not None:
        query = query.where(Transaction.category_id == category_id)

    if transaction_type is not None:
        query = query.where(Transaction.type == transaction_type)

    if start_date is not None:
        query = query.where(Transaction.date >= start_date)

    if end_date is not None:
        query = query.where(Transaction.date <= end_date)

    query = query.order_by(
        Transaction.date.desc(),
        Transaction.created_at.desc(),
    )

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_transaction_summary(
    db: AsyncSession,
    user_id: int,
    account_id: int | None = None,
    category_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    income_sum = func.coalesce(
        func.sum(
            case(
                (
                    Transaction.type == TransactionType.income,
                    Transaction.amount,
                ),
                else_=Decimal("0"),
            )
        ),
        Decimal("0.00"),
    )

    expense_sum = func.coalesce(
        func.sum(
            case(
                (
                    Transaction.type == TransactionType.expense,
                    Transaction.amount,
                ),
                else_=Decimal("0"),
            )
        ),
        Decimal("0.00"),
    )

    query = select(
        income_sum,
        expense_sum,
        func.count(Transaction.id),
    ).where(
        Transaction.user_id == user_id,
        ~Transaction.is_deleted,
    )

    if account_id is not None:
        query = query.where(Transaction.account_id == account_id)

    if category_id is not None:
        query = query.where(Transaction.category_id == category_id)

    if start_date is not None:
        query = query.where(Transaction.date >= start_date)

    if end_date is not None:
        query = query.where(Transaction.date <= end_date)

    result = await db.execute(query)
    row = result.one()

    total_income = row[0]
    total_expense = row[1]

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net": total_income - total_expense,
        "transaction_count": row[2],
    }


async def get_daily_summary(
    db: AsyncSession,
    user_id: int,
    start_date: date,
    end_date: date,
    account_id: int | None = None,
) -> list[dict]:
    income_sum = func.coalesce(
        func.sum(
            case(
                (
                    Transaction.type == TransactionType.income,
                    Transaction.amount,
                ),
                else_=Decimal("0"),
            )
        ),
        Decimal("0.00"),
    )

    expense_sum = func.coalesce(
        func.sum(
            case(
                (
                    Transaction.type == TransactionType.expense,
                    Transaction.amount,
                ),
                else_=Decimal("0"),
            )
        ),
        Decimal("0.00"),
    )

    query = (
        select(
            Transaction.date,
            income_sum,
            expense_sum,
        )
        .where(
            Transaction.user_id == user_id,
            ~Transaction.is_deleted,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
        )
        .group_by(Transaction.date)
        .order_by(Transaction.date)
    )

    if account_id is not None:
        query = query.where(Transaction.account_id == account_id)

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "date": row[0],
            "income": row[1],
            "expense": row[2],
            "net": row[1] - row[2],
        }
        for row in rows
    ]


async def update_transaction(
    db: AsyncSession,
    transaction: Transaction,
    data: TransactionUpdate,
) -> Transaction:
    old_amount = transaction.amount
    old_account_id = transaction.account_id

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)

    new_amount = transaction.amount
    new_account_id = transaction.account_id

    if new_amount != old_amount or new_account_id != old_account_id:
        if transaction.type == TransactionType.income:
            old_change = -old_amount
            new_change = new_amount
        else:
            old_change = old_amount
            new_change = -new_amount

        await db.execute(
            update(Account)
            .where(Account.id == old_account_id)
            .values(balance=Account.balance + old_change)
        )

        await db.execute(
            update(Account)
            .where(Account.id == new_account_id)
            .values(balance=Account.balance + new_change)
        )

    await db.commit()
    await db.refresh(transaction)
    await invalidate_reports_cache(transaction.user_id)
    return transaction


async def soft_delete_transaction(
    db: AsyncSession,
    transaction: Transaction,
) -> Transaction:
    if transaction.type == TransactionType.income:
        balance_change = -transaction.amount
    else:
        balance_change = transaction.amount

    await db.execute(
        update(Account)
        .where(Account.id == transaction.account_id)
        .values(balance=Account.balance + balance_change)
    )

    transaction.is_deleted = True
    transaction.deleted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(transaction)
    await invalidate_reports_cache(transaction.user_id)
    return transaction


async def create_transfer(
    db: AsyncSession,
    user_id: int,
    from_account_id: int,
    to_account_id: int,
    amount: Decimal,
    transfer_date: date,
    note: str | None = None,
) -> tuple[Transaction, Transaction]:
    ordered_ids = sorted([from_account_id, to_account_id])

    result = await db.execute(
        select(Account)
        .where(Account.id.in_(ordered_ids))
        .with_for_update()
        .order_by(Account.id)
    )
    locked_accounts = {a.id: a for a in result.scalars().all()}

    from_transaction = Transaction(
        user_id=user_id,
        account_id=from_account_id,
        category_id=None,
        type=TransactionType.expense,
        amount=amount,
        date=transfer_date,
        note=note,
    )
    db.add(from_transaction)

    to_transaction = Transaction(
        user_id=user_id,
        account_id=to_account_id,
        category_id=None,
        type=TransactionType.income,
        amount=amount,
        date=transfer_date,
        note=note,
    )
    db.add(to_transaction)

    await db.flush()

    from_transaction.transfer_id = to_transaction.id
    to_transaction.transfer_id = from_transaction.id

    locked_accounts[from_account_id].balance -= amount
    locked_accounts[to_account_id].balance += amount

    await db.commit()
    await db.refresh(from_transaction)
    await db.refresh(to_transaction)
    await invalidate_reports_cache(user_id)

    return from_transaction, to_transaction
