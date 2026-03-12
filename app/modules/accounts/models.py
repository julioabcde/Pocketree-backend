import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Index,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin


__all__ = ["Account", "AccountType", "NEGATIVE_ALLOWED_TYPES"]


class AccountType(str, enum.Enum):
    cash = "cash"
    bank_account = "bank_account"
    e_wallet = "e_wallet"
    credit_card = "credit_card"


NEGATIVE_ALLOWED_TYPES: set[AccountType] = {
    AccountType.credit_card,
}


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    __table_args__ = (
        Index(
            "ix_accounts_unique_active",
            "user_id",
            text("LOWER(name)"),
            "type",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    type: Mapped[AccountType] = mapped_column(
        SAEnum(AccountType, name="account_type"), nullable=False
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )

    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    @property
    def allows_negative_balance(self) -> bool:
        """Check if the account type permits negative balances."""
        return self.type in NEGATIVE_ALLOWED_TYPES

    def __repr__(self):
        return (
            f"<Account(id={self.id}, name={self.name!r},"
            f" type={self.type.value}, balance={self.balance})>"
        )
