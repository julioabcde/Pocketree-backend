import calendar
from datetime import date as Date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from zoneinfo import ZoneInfo

from loguru import logger
from sqlalchemy import update as sa_update
from app.modules.accounts.models import Account

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recurring.models import (
    RecurringFrequency,
    RecurringTransaction,
)
from app.modules.recurring.schemas import RecurringCreate, RecurringUpdate
from app.modules.transactions.models import TransactionType

__all__ = [
    "calculate_next_date",
    "create_recurring",
    "get_recurring_by_id",
    "get_recurring_by_user",
    "get_recurring_summary",
    "update_recurring",
    "deactivate_recurring",
    "execute_single_recurring",
    "process_due_recurring",
]


def calculate_next_date(
    frequency: RecurringFrequency,
    current_due_date: Date,
    day_of_week: int | None = None,
    day_of_month: int | None = None,
    month_of_year: int | None = None,
) -> Date:
    if frequency == RecurringFrequency.daily:
        return current_due_date + timedelta(days=1)

    elif frequency == RecurringFrequency.weekly:
        return current_due_date + timedelta(weeks=1)

    elif frequency == RecurringFrequency.monthly:
        next_month = current_due_date.month + 1
        next_year = current_due_date.year

        if next_month > 12:
            next_month = 1
            next_year += 1

        last_day = calendar.monthrange(next_year, next_month)[1]
        actual_day = min(day_of_month, last_day)
        return Date(next_year, next_month, actual_day)

    elif frequency == RecurringFrequency.yearly:
        next_year = current_due_date.year + 1
        last_day = calendar.monthrange(next_year, month_of_year)[1]
        actual_day = min(day_of_month, last_day)
        return Date(next_year, month_of_year, actual_day)


def calculate_initial_due_date(
    frequency: RecurringFrequency,
    start_date: Date,
    day_of_week: int | None = None,
    day_of_month: int | None = None,
    month_of_year: int | None = None,
) -> Date:
    if frequency == RecurringFrequency.daily:
        return start_date

    elif frequency == RecurringFrequency.weekly:
        current_dow = start_date.weekday()
        days_ahead = day_of_week - current_dow
        if days_ahead < 0:
            days_ahead += 7
        return start_date + timedelta(days=days_ahead)

    elif frequency == RecurringFrequency.monthly:
        last_day = calendar.monthrange(start_date.year, start_date.month)[1]
        actual_day = min(day_of_month, last_day)

        if start_date.day <= actual_day:
            return Date(start_date.year, start_date.month, actual_day)
        else:
            return calculate_next_date(
                frequency,
                start_date,
                day_of_month=day_of_month,
            )

    elif frequency == RecurringFrequency.yearly:
        last_day = calendar.monthrange(start_date.year, month_of_year)[1]
        actual_day = min(day_of_month, last_day)
        candidate = Date(start_date.year, month_of_year, actual_day)

        if candidate >= start_date:
            return candidate
        else:
            return calculate_next_date(
                frequency,
                candidate,
                day_of_month=day_of_month,
                month_of_year=month_of_year,
            )


async def create_recurring(
    db: AsyncSession,
    user_id: int,
    data: RecurringCreate,
) -> RecurringTransaction:
    next_due = calculate_initial_due_date(
        frequency=data.frequency,
        start_date=data.start_date,
        day_of_week=data.day_of_week,
        day_of_month=data.day_of_month,
        month_of_year=data.month_of_year,
    )

    recurring = RecurringTransaction(
        user_id=user_id,
        account_id=data.account_id,
        category_id=data.category_id,
        type=data.type,
        amount=data.amount,
        frequency=data.frequency,
        day_of_week=data.day_of_week,
        day_of_month=data.day_of_month,
        month_of_year=data.month_of_year,
        start_date=data.start_date,
        end_date=data.end_date,
        next_due_date=next_due,
        timezone=data.timezone,
        auto_create=data.auto_create,
        max_occurrences=data.max_occurrences,
        note=data.note,
    )

    db.add(recurring)
    await db.commit()
    await db.refresh(recurring)
    return recurring


async def get_recurring_by_id(
    db: AsyncSession, recurring_id: int
) -> RecurringTransaction | None:
    result = await db.execute(
        select(RecurringTransaction).where(
            RecurringTransaction.id == recurring_id,
        )
    )
    return result.scalar_one_or_none()


async def get_recurring_by_user(
    db: AsyncSession,
    user_id: int,
    status: Literal["active", "inactive", "all"] = "active",
) -> list[RecurringTransaction]:
    query = select(RecurringTransaction).where(
        RecurringTransaction.user_id == user_id
    )

    if status == "active":
        query = query.where(RecurringTransaction.is_active.is_(True))
    elif status == "inactive":
        query = query.where(RecurringTransaction.is_active.is_(False))

    if status == "all":
        query = query.order_by(
            RecurringTransaction.is_active.desc(),
            RecurringTransaction.next_due_date.asc(),
        )
    else:
        query = query.order_by(
            RecurringTransaction.next_due_date.asc(),
        )

    result = await db.execute(query)
    return list(result.scalars().all())


def _monthly_equivalent_amount(recurring: RecurringTransaction) -> Decimal:
    if recurring.frequency == RecurringFrequency.daily:
        return recurring.amount * Decimal("30")
    if recurring.frequency == RecurringFrequency.weekly:
        return recurring.amount * Decimal("4.345")
    if recurring.frequency == RecurringFrequency.monthly:
        return recurring.amount
    if recurring.frequency == RecurringFrequency.yearly:
        return recurring.amount / Decimal("12")

    return Decimal("0.00")


async def get_recurring_summary(
    db: AsyncSession,
    user_id: int,
) -> dict:
    result = await db.execute(
        select(RecurringTransaction).where(
            RecurringTransaction.user_id == user_id,
            RecurringTransaction.is_active.is_(True),
        )
    )

    recurring_items = list(result.scalars().all())

    total_monthly_income = Decimal("0.00")
    total_monthly_expense = Decimal("0.00")
    for recurring in recurring_items:
        monthly_amount = _monthly_equivalent_amount(recurring)
        if recurring.type == TransactionType.income:
            total_monthly_income += monthly_amount
        else:
            total_monthly_expense += monthly_amount

    total_monthly_income = total_monthly_income.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    total_monthly_expense = total_monthly_expense.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    net_monthly_commitment = (total_monthly_income - total_monthly_expense).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return {
        "total_monthly_income": total_monthly_income,
        "total_monthly_expense": total_monthly_expense,
        "net_monthly_commitment": net_monthly_commitment,
    }


async def update_recurring(
    db: AsyncSession,
    recurring: RecurringTransaction,
    data: RecurringUpdate,
) -> RecurringTransaction:
    update_data = data.model_dump(exclude_unset=True)

    if "end_date" in update_data and update_data["end_date"] is not None:
        if update_data["end_date"] <= recurring.start_date:
            raise ValueError(
                f"end_date must be after start_date ({recurring.start_date})"
            )

    for field, value in update_data.items():
        setattr(recurring, field, value)

    await db.commit()
    await db.refresh(recurring)
    return recurring


async def deactivate_recurring(
    db: AsyncSession,
    recurring: RecurringTransaction,
) -> RecurringTransaction:
    recurring.is_active = False

    await db.commit()
    await db.refresh(recurring)
    return recurring


async def execute_single_recurring(
    db: AsyncSession,
    recurring: RecurringTransaction,
) -> bool:

    if not recurring.is_active:
        logger.debug(f"Recurring {recurring.id}: skipped (inactive)")
        return False

    if recurring.last_run_at is not None:
        last_run_date = recurring.last_run_at.date()
        if last_run_date >= recurring.next_due_date:
            logger.debug(
                f"Recurring {recurring.id}: skipped "
                f"(already ran on {last_run_date})"
            )
            return False

    if recurring.has_reached_limit:
        recurring.is_active = False
        logger.info(
            f"Recurring {recurring.id}: deactivated "
            f"(reached {recurring.max_occurrences} occurrences)"
        )
        return False

    if recurring.is_expired:
        recurring.is_active = False
        logger.info(
            f"Recurring {recurring.id}: deactivated "
            f"(expired on {recurring.end_date})"
        )
        return False

    if recurring.auto_create:
        from app.modules.transactions.models import Transaction

        transaction = Transaction(
            user_id=recurring.user_id,
            account_id=recurring.account_id,
            category_id=recurring.category_id,
            type=recurring.type,
            amount=recurring.amount,
            date=recurring.next_due_date,
            note=recurring.note,
        )
        db.add(transaction)

        if recurring.type == TransactionType.income:
            balance_change = recurring.amount
        else:
            balance_change = -recurring.amount

        await db.execute(
            sa_update(Account)
            .where(Account.id == recurring.account_id)
            .values(balance=Account.balance + balance_change)
        )

        logger.info(
            f"Recurring {recurring.id}: created {recurring.type.value} "
            f"transaction {recurring.amount} for account "
            f"{recurring.account_id} on {recurring.next_due_date}"
        )
    else:
        # Future: send push notification
        logger.info(
            f"Recurring {recurring.id}: reminder mode "
            f"(notification not implemented)"
        )

    user_tz = ZoneInfo(recurring.timezone)
    recurring.last_run_at = datetime.now(user_tz)
    recurring.occurrence_count += 1
    recurring.next_due_date = calculate_next_date(
        frequency=recurring.frequency,
        current_due_date=recurring.next_due_date,
        day_of_week=recurring.day_of_week,
        day_of_month=recurring.day_of_month,
        month_of_year=recurring.month_of_year,
    )

    if recurring.has_reached_limit:
        recurring.is_active = False
        logger.info(
            f"Recurring {recurring.id}: deactivated "
            f"(completed {recurring.occurrence_count}/"
            f"{recurring.max_occurrences} occurrences)"
        )

    if recurring.end_date and recurring.next_due_date > recurring.end_date:
        recurring.is_active = False
        logger.info(
            f"Recurring {recurring.id}: deactivated "
            f"(next due {recurring.next_due_date} exceeds "
            f"end date {recurring.end_date})"
        )

    return True


async def process_due_recurring(db: AsyncSession) -> dict:

    async with db.begin(): 

        result = await db.execute(
            select(RecurringTransaction)
            .where(
                RecurringTransaction.next_due_date <= func.current_date(),
                RecurringTransaction.is_active,
            )
            .with_for_update(skip_locked=True)  
        )

        candidates = list(result.scalars().all())

        logger.info(
            f"Recurring scheduler: found {len(candidates)} candidates"
        )

    executed = 0
    skipped = 0
    errors = 0

    for recurring in candidates:
        user_today = datetime.now(
            ZoneInfo(recurring.timezone)
        ).date()

        if recurring.next_due_date > user_today:
            skipped += 1
            continue

        try:
            async with db.begin():

                iteration = 0
                max_iterations = 100

                while recurring.next_due_date <= user_today:
                    if iteration > max_iterations:
                        logger.error(
                            f"Recurring {recurring.id}: infinite loop detected"
                        )
                        break

                    was_executed = await execute_single_recurring(
                        db, recurring
                    )

                    if not was_executed:
                        skipped += 1
                        break

                    executed += 1
                    iteration += 1

                await db.refresh(recurring)

        except Exception as e:
            errors += 1
            logger.error(
                f"Recurring {recurring.id} failed: {e}"
            )
            await db.rollback()

    summary = {
        "candidates": len(candidates),
        "executed": executed,
        "skipped": skipped,
        "errors": errors,
    }

    logger.info(f"Recurring scheduler completed: {summary}")

    return summary
