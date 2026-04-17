import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin

__all__ = ["Transaction", "TransactionType"]

class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"
    
class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    
    __table_args__ = (
        Index(
            "ix_transactions_user_date",
            "user_id", "date", "created_at",
            postgresql_where=text("is_deleted = false"),
        ),
        Index(
            "ix_tx_reports_user_date_active_non_transfer",
            "user_id",
            "date",
            postgresql_where=text("is_deleted = false AND transfer_id IS NULL"),
        ),
        Index(
            "ix_tx_reports_user_account_date_active_non_transfer",
            "user_id",
            "account_id",
            "date",
            postgresql_where=text("is_deleted = false AND transfer_id IS NULL"),
        ),
        Index(
            "ix_tx_reports_user_type_date_amount_active_non_transfer",
            "user_id",
            "type",
            "date",
            text("amount DESC"),
            postgresql_where=text("is_deleted = false AND transfer_id IS NULL"),
        ),
        Index(
            "ix_tx_reports_user_category_date_active_non_transfer",
            "user_id",
            "category_id",
            "date",
            postgresql_where=text("is_deleted = false AND transfer_id IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("accounts.id"), nullable=False, index=True
    )

    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True, index=True
    )

    type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, name="transaction_type"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    note: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )


    transfer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("transactions.id"), nullable=True
    )


    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    @property
    def is_transfer(self) -> bool:
        """True if this transaction is part of a transfer pair."""
        return self.transfer_id is not None

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, type={self.type.value}, "
            f"amount={self.amount}, account_id={self.account_id})>"
        )
