from datetime import date as Date, datetime
from decimal import Decimal

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
    UniqueConstraint,
    func,
    text,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin

__all__ = [
    "SplitBill",
    "SplitBillCharge",
    "SplitBillItem",
    "SplitBillParticipant",
    "SplitBillDebt",
    "SplitBillSettlement",
    "SplitBillParticipantItem",
]


class SplitBill(Base, TimestampMixin):
    __tablename__ = "split_bills"

    __table_args__ = (
        Index(
            "ix_split_bills_user_active",
            "user_id",
            postgresql_where=text("is_deleted = false"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )

    date: Mapped[Date] = mapped_column(SADate, nullable=False)

    note: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    receipt_image_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, default=None
    )

    transaction_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("transactions.id"), nullable=True, default=None
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    def __repr__(self) -> str:
        return (
            f"<SplitBill(id={self.id}, title={self.title!r}, "
            f"total={self.total_amount})>"
        )


class SplitBillCharge(Base):
    __tablename__ = "split_bill_charges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    bill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(String(50), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<SplitBillCharge(id={self.id}, type={self.type!r}, "
            f"name={self.name!r}, amount={self.amount})>"
        )


class SplitBillItem(Base):
    __tablename__ = "split_bill_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    bill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    price: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<SplitBillItem(id={self.id}, name={self.name!r}, "
            f"subtotal={self.subtotal})>"
        )


class SplitBillParticipant(Base):
    __tablename__ = "split_bill_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    bill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, default=None
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    is_payer: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )

    final_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<SplitBillParticipant(id={self.id}, name={self.name!r}, "
            f"paid={self.paid_amount}, owes={self.final_amount})>"
        )


class SplitBillDebt(Base):
    __tablename__ = "split_bill_debts"

    __table_args__ = (
        Index(
            "ix_split_bill_debts_bill_debtor",
            "bill_id",
            "debtor_participant_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    bill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    debtor_participant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bill_participants.id", ondelete="CASCADE"),
        nullable=False,
    )

    creditor_participant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bill_participants.id", ondelete="CASCADE"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )

    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    @property
    def is_settled(self) -> bool:
        return self.remaining_amount <= Decimal("0.00")

    def __repr__(self) -> str:
        return (
            f"<SplitBillDebt(id={self.id}, "
            f"debtor={self.debtor_participant_id}, "
            f"creditor={self.creditor_participant_id}, "
            f"remaining={self.remaining_amount})>"
        )


class SplitBillSettlement(Base):
    __tablename__ = "split_bill_settlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    bill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    debt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bill_debts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    from_participant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bill_participants.id", ondelete="CASCADE"),
        nullable=False,
    )

    to_participant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bill_participants.id", ondelete="CASCADE"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )

    transaction_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("transactions.id"), nullable=True, default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<SplitBillSettlement(id={self.id}, "
            f"from={self.from_participant_id}, "
            f"to={self.to_participant_id}, "
            f"amount={self.amount})>"
        )


class SplitBillParticipantItem(Base):
    __tablename__ = "split_bill_participant_items"

    __table_args__ = (
        UniqueConstraint(
            "participant_id",
            "item_id",
            name="uq_split_bill_participant_items_participant_item",
        ),
        CheckConstraint(
            "portion > 0",
            name="ck_split_bill_participant_items_portion_positive",
        ),
        CheckConstraint(
            "allocated_subtotal >= 0",
            name="ck_split_bill_participant_items_allocated_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    bill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    participant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bill_participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("split_bill_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    portion: Mapped[int] = mapped_column(Integer, nullable=False)

    allocated_subtotal: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=Decimal("0.00"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<SplitBillParticipantItem(id={self.id}, "
            f"participant_id={self.participant_id}, item_id={self.item_id}, "
            f"portion={self.portion}, subtotal={self.allocated_subtotal})>"
        )
