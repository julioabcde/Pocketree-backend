from datetime import date as Date, datetime
from decimal import Decimal
from zoneinfo import available_timezones

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.recurring.models import RecurringFrequency
from app.modules.transactions.models import TransactionType

__all__ = [
    "RecurringCreate",
    "RecurringUpdate",
    "RecurringResponse",
    "RecurringSummary",
]

class RecurringCreate(BaseModel):
    account_id: int
    category_id: int | None = None
    type: TransactionType
    amount: Decimal = Field(
        gt=Decimal("0"),
        decimal_places=2,
    )
    frequency: RecurringFrequency
    day_of_week: int | None = Field(
        default=None, ge=0, le=6,
        description="0=Monday, 6=Sunday. Required for weekly.",
    )
    day_of_month: int | None = Field(
        default=None, ge=1, le=31,
        description="1-31. Required for monthly/yearly. "
        "For months with fewer days, capped to last day.",
    )
    month_of_year: int | None = Field(
        default=None, ge=1, le=12,
        description="1-12. Required for yearly.",
    )
    start_date: Date
    end_date: Date | None = None
    timezone: str = Field(
        default="UTC", max_length=50,
    )
    auto_create: bool = True
    max_occurrences: int | None = Field(
        default=None, ge=1,
        description="Stop after N executions. Null = unlimited. "
        "If both max_occurrences and end_date are set, "
        "whichever triggers first takes effect.",
    )
    note: str | None = Field(
        default=None, max_length=500,
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        value = value.strip()
        if value not in available_timezones():
            raise ValueError(
                f"Invalid timezone: '{value}'. "
                f"Use IANA format like 'Asia/Jakarta' or 'UTC'."
            )
        return value

    @field_validator("note")
    @classmethod
    def sanitize_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value if value else None

    @model_validator(mode="after")
    def validate_frequency_fields(self) -> "RecurringCreate":
        f = self.frequency

        if f == RecurringFrequency.daily:
            if self.day_of_week is not None:
                raise ValueError(
                    "day_of_week is not used for daily frequency"
                )
            if self.day_of_month is not None:
                raise ValueError(
                    "day_of_month is not used for daily frequency"
                )
            if self.month_of_year is not None:
                raise ValueError(
                    "month_of_year is not used for daily frequency"
                )

        elif f == RecurringFrequency.weekly:
            if self.day_of_week is None:
                raise ValueError(
                    "day_of_week is required for weekly frequency"
                )
            if self.day_of_month is not None:
                raise ValueError(
                    "day_of_month is not used for weekly frequency"
                )
            if self.month_of_year is not None:
                raise ValueError(
                    "month_of_year is not used for weekly frequency"
                )

        elif f == RecurringFrequency.monthly:
            if self.day_of_month is None:
                raise ValueError(
                    "day_of_month is required for monthly frequency"
                )
            if self.day_of_week is not None:
                raise ValueError(
                    "day_of_week is not used for monthly frequency"
                )
            if self.month_of_year is not None:
                raise ValueError(
                    "month_of_year is not used for monthly frequency"
                )

        elif f == RecurringFrequency.yearly:
            if self.day_of_month is None:
                raise ValueError(
                    "day_of_month is required for yearly frequency"
                )
            if self.month_of_year is None:
                raise ValueError(
                    "month_of_year is required for yearly frequency"
                )
            if self.day_of_week is not None:
                raise ValueError(
                    "day_of_week is not used for yearly frequency"
                )

        if self.end_date is not None:
            if self.end_date <= self.start_date:
                raise ValueError(
                    "end_date must be after start_date"
                )

        return self

class RecurringUpdate(BaseModel):
    category_id: int | None = None
    amount: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
        decimal_places=2,
    )
    end_date: Date | None = None
    timezone: str | None = Field(
        default=None, max_length=50,
    )
    auto_create: bool | None = None
    max_occurrences: int | None = Field(
        default=None, ge=1,
    )
    is_active: bool | None = None
    note: str | None = Field(
        default=None, max_length=500,
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if value not in available_timezones():
            raise ValueError(
                f"Invalid timezone: '{value}'. "
                f"Use IANA format like 'Asia/Jakarta' or 'UTC'."
            )
        return value

    @field_validator("note")
    @classmethod
    def sanitize_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value if value else None

class RecurringResponse(BaseModel):
    id: int
    account_id: int
    category_id: int | None
    type: TransactionType
    amount: Decimal
    frequency: RecurringFrequency
    day_of_week: int | None
    day_of_month: int | None
    month_of_year: int | None
    start_date: Date
    end_date: Date | None
    next_due_date: Date
    last_run_at: datetime | None
    timezone: str
    auto_create: bool
    max_occurrences: int | None
    occurrence_count: int
    is_active: bool
    note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecurringSummary(BaseModel):
    total_monthly_income: Decimal
    total_monthly_expense: Decimal
    net_monthly_commitment: Decimal
