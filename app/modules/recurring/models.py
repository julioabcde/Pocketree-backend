import enum
from datetime import date as Date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date as SADate,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin
from app.modules.transactions.models import TransactionType

__all__ = ["RecurringTransaction", "RecurringFrequency"]


class RecurringFrequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class RecurringTransaction(Base, TimestampMixin):
    __tablename__ = "recurring_transactions"

    __table_args__ = (
        Index(
            "ix_recurring_next_due_active",
            "next_due_date",
            postgresql_where=text("is_active = true"),
        ),
        Index(
            "ix_recurring_user_due",
            "user_id", "next_due_date",
            postgresql_where=text("is_active = true"),
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_recurring_amount_positive",
        ),
        CheckConstraint(
            "day_of_week BETWEEN 0 AND 6 OR day_of_week IS NULL",
            name="ck_recurring_day_of_week_range",
        ),
        CheckConstraint(
            "day_of_month BETWEEN 1 AND 31 OR day_of_month IS NULL",
            name="ck_recurring_day_of_month_range",
        ),
        CheckConstraint(
            "month_of_year BETWEEN 1 AND 12 OR month_of_year IS NULL",
            name="ck_recurring_month_of_year_range",
        ),
        CheckConstraint(
            "next_due_date >= start_date",
            name="ck_recurring_next_due_after_start",
        ),
        CheckConstraint(
            "occurrence_count >= 0",
            name="ck_recurring_occurrence_not_negative",
        ),
    )


    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )


    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )


    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("accounts.id"), nullable=False
    )

    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )

    type: Mapped[TransactionType] = mapped_column(
        PGEnum(TransactionType, name="transaction_type", create_type=False),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )

    note: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )


    frequency: Mapped[RecurringFrequency] = mapped_column(
        SAEnum(RecurringFrequency, name="recurring_frequency"), nullable=False
    )

    day_of_week: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    day_of_month: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    month_of_year: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    start_date: Mapped[Date] = mapped_column(
        SADate, nullable=False
    )

    end_date: Mapped[Date | None] = mapped_column(
        SADate, nullable=True
    )

    next_due_date: Mapped[Date] = mapped_column(
        SADate, nullable=False
    )

    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, default="UTC"
    )


    auto_create: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    max_occurrences: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    occurrence_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


    @property
    def has_reached_limit(self) -> bool:
        if self.max_occurrences is None:
            return False
        return self.occurrence_count >= self.max_occurrences

    @property
    def is_expired(self) -> bool:
        if self.end_date is None:
            return False
        user_today = datetime.now(ZoneInfo(self.timezone)).date()
        return user_today > self.end_date

    def __repr__(self) -> str:
        return (
            f"<RecurringTransaction(id={self.id}, "
            f"frequency={self.frequency.value}, "
            f"amount={self.amount}, "
            f"next_due={self.next_due_date})>"
        )
