from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.modules.accounts.models import AccountType

__all__ = [
    "AccountCreate",
    "AccountUpdate",
    "AccountResponse",
    "AccountSummary",
]


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: AccountType
    initial_balance: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        decimal_places=2,
        description="Starting balance. Must be >= 0.00",
    )

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        return " ".join(value.split())


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: AccountType | None = None

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return " ".join(value.split())


class AccountResponse(BaseModel):
    id: int
    name: str
    type: AccountType
    balance: Decimal
    initial_balance: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AccountSummary(BaseModel):
    total_balance: Decimal
    accounts_count: int
