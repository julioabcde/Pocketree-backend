from datetime import date as Date
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.modules.transactions.models import TransactionType

__all__ = [
    "TransactionCreate",
    "TransactionUpdate",
    "TransactionTransfer",
    "TransactionResponse",
    "TransferResponse",
    "TransactionSummary",
    "DailySummary",
]


class TransactionCreate(BaseModel):
    account_id: int
    category_id: int | None = None
    type: TransactionType
    amount: Decimal = Field(
        gt=Decimal("0"),
        decimal_places=2,
    )
    date: Date
    note: str | None = Field(default=None, max_length=500)

    @field_validator("note")
    @classmethod
    def sanitize_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value if value else None


class TransactionTransfer(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal = Field(
        gt=Decimal("0"),
        decimal_places=2,
    )
    date: Date
    note: str | None = Field(default=None, max_length=500)

    @field_validator("to_account_id")
    @classmethod
    def accounts_must_differ(cls, value: int, info) -> int:
        if info.data.get("from_account_id") == value:
            raise ValueError("Cannot transfer to the same account")
        return value

    @field_validator("note")
    @classmethod
    def sanitize_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value if value else None


class TransactionUpdate(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    amount: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
        decimal_places=2,
    )
    date: Date | None = None
    note: str | None = Field(default=None, max_length=500)

    @field_validator("note")
    @classmethod
    def sanitize_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value if value else None


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    category_id: int | None
    type: TransactionType
    amount: Decimal
    date: Date
    note: str | None
    transfer_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransferResponse(BaseModel):
    from_transaction: TransactionResponse
    to_transaction: TransactionResponse
    message: str = "Transfer completed successfully"


class TransactionSummary(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
    transaction_count: int
    
    
class DailySummary(BaseModel):
    date: Date
    income: Decimal
    expense: Decimal
    net: Decimal
