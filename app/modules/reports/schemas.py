from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel

from app.modules.accounts.models import AccountType

__all__ = [
    "ReportGroupBy",
    "MetricDelta",
    "CountDelta",
    "OverviewPeriod",
    "OverviewDelta",
    "OverviewResponse",
    "CashflowTrendItem",
    "CategoryBreakdownItem",
    "CategoryBreakdownResponse",
    "AccountBreakdownItem",
    "AccountBreakdownResponse",
    "TopTransactionItem",
    "PeriodComparisonPeriod",
    "PeriodComparisonDelta",
    "PeriodComparisonResponse",
]


class ReportGroupBy(str, Enum):
    day = "day"
    week = "week"
    month = "month"


class MetricDelta(BaseModel):
    amount: Decimal
    percent: Decimal | None


class CountDelta(BaseModel):
    amount: int
    percent: Decimal | None


class OverviewPeriod(BaseModel):
    income: Decimal
    expense: Decimal
    net: Decimal


class OverviewDelta(BaseModel):
    income: MetricDelta
    expense: MetricDelta
    net: MetricDelta


class OverviewResponse(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
    transaction_count: int
    savings_rate: Decimal | None
    previous_period: OverviewPeriod
    delta: OverviewDelta


class CashflowTrendItem(BaseModel):
    period: str
    start_date: date
    end_date: date
    income: Decimal
    expense: Decimal
    net: Decimal
    cumulative_net: Decimal


class CategoryBreakdownItem(BaseModel):
    category_id: int | None
    name: str
    color: str
    icon: str
    amount: Decimal
    percentage: Decimal | None
    transaction_count: int


class CategoryBreakdownResponse(BaseModel):
    total_amount: Decimal
    items: list[CategoryBreakdownItem]


class AccountBreakdownItem(BaseModel):
    account_id: int
    account_name: str
    account_type: AccountType
    amount: Decimal
    percentage: Decimal | None
    transaction_count: int


class AccountBreakdownResponse(BaseModel):
    total_amount: Decimal
    items: list[AccountBreakdownItem]


class TopTransactionItem(BaseModel):
    transaction_id: int
    date: date
    amount: Decimal
    account: str
    category: str
    note: str | None


class PeriodComparisonPeriod(BaseModel):
    income: Decimal
    expense: Decimal
    net: Decimal
    transaction_count: int


class PeriodComparisonDelta(BaseModel):
    income: MetricDelta
    expense: MetricDelta
    net: MetricDelta
    transaction_count: CountDelta


class PeriodComparisonResponse(BaseModel):
    current_period: PeriodComparisonPeriod
    previous_period: PeriodComparisonPeriod
    delta: PeriodComparisonDelta
