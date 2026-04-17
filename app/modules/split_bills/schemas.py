from datetime import date as Date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

__all__ = [
    "SplitBillCreate",
    "SplitBillChargeInput",
    "SplitBillItemInput",
    "SplitBillParticipantInput",
    "SplitBillCalculateRequest",
    "ParticipantShare",
    "SplitBillSettlementInput",
    "SplitBillResponse",
    "SplitBillDetailResponse",
    "SplitBillCalculateResponse",
    "DebtSummary",
    "DebtSummaryItem",
    "SplitBillChargeResponse",
    "SplitBillItemResponse",
    "SplitBillParticipantResponse",
    "SplitBillParticipantItemResponse",
    "SplitBillParticipantDetailResponse",
    "SplitBillDebtResponse",
    "SplitBillSettlementResponse",
    "SplitBillSettlementSummaryResponse",
    "SplitBillSummaryResponse",
    "ReceiptScanItem",
    "ReceiptScanCharge",
    "ReceiptScanResponse",
]


class SplitBillItemInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price: Decimal = Field(
        gt=Decimal("0"),
        decimal_places=2,
    )
    quantity: int = Field(default=1, ge=1)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        return " ".join(value.split())


class SplitBillChargeInput(BaseModel):
    type: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=Decimal("0"), decimal_places=2)

    @field_validator("type")
    @classmethod
    def sanitize_type(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        return " ".join(value.split())


class SplitBillCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    date: Date
    note: str | None = Field(default=None, max_length=500)
    receipt_image_url: str | None = Field(default=None, max_length=500)
    items: list[SplitBillItemInput] = Field(min_length=1)
    charges: list[SplitBillChargeInput] = Field(default=[])

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("note")
    @classmethod
    def sanitize_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value if value else None


class SplitBillParticipantInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    is_payer: bool = False
    paid_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        decimal_places=2,
    )
    user_id: int | None = None

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        return " ".join(value.split())


class ParticipantShare(BaseModel):
    participant_index: int = Field(
        ge=0,
        description="Index into the participants list (0-based)",
    )
    item_ids: list[int] = Field(default=[])
    custom_amount: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        decimal_places=2,
    )
    share_portions: dict[str, int] = Field(
        default={},
        description="Per-item portion. Key=item_id as string, "
        "value=portions this person takes. "
        "E.g. {'3': 3} means 3 out of total portions.",
    )


class SplitBillCalculateRequest(BaseModel):
    participants: list[SplitBillParticipantInput] = Field(min_length=2)
    shares: list[ParticipantShare] = Field(default=[])
    account_id: int | None = None


class SplitBillSettlementInput(BaseModel):
    amount: Decimal = Field(
        gt=Decimal("0"),
        decimal_places=2,
        description="Payment amount. Must not exceed remaining debt.",
    )
    account_id: int | None = None


class SplitBillChargeResponse(BaseModel):
    id: int
    type: str
    name: str
    amount: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class SplitBillItemResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    quantity: int
    subtotal: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class SplitBillParticipantResponse(BaseModel):
    id: int
    user_id: int | None
    name: str
    is_payer: bool
    paid_amount: Decimal
    final_amount: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class SplitBillParticipantItemResponse(BaseModel):
    item_id: int
    item_name: str
    portion: int
    allocated_subtotal: Decimal


class SplitBillParticipantDetailResponse(SplitBillParticipantResponse):
    items: list[SplitBillParticipantItemResponse] = Field(default_factory=list)


class SplitBillDebtResponse(BaseModel):
    id: int
    debtor_participant_id: int
    creditor_participant_id: int
    amount: Decimal
    remaining_amount: Decimal
    is_settled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SplitBillSettlementResponse(BaseModel):
    id: int
    debt_id: int
    from_participant_id: int
    to_participant_id: int
    amount: Decimal
    transaction_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SplitBillSettlementSummaryResponse(BaseModel):
    total_debt_amount: Decimal
    remaining_debt_amount: Decimal
    settled_debt_count: int
    total_debt_count: int
    settlement_count: int
    settled_amount: Decimal


class SplitBillResponse(BaseModel):
    id: int
    title: str
    subtotal: Decimal
    total_amount: Decimal
    date: Date
    note: str | None
    receipt_image_url: str | None
    transaction_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SplitBillDetailResponse(BaseModel):
    id: int
    title: str
    subtotal: Decimal
    total_amount: Decimal
    date: Date
    note: str | None
    receipt_image_url: str | None
    transaction_id: int | None
    items: list[SplitBillItemResponse]
    charges: list[SplitBillChargeResponse]
    participants: list[SplitBillParticipantDetailResponse]
    debts: list[SplitBillDebtResponse]
    settlements: list[SplitBillSettlementResponse]
    paid_participant_count: int
    total_non_payer_count: int
    has_calculation: bool
    is_fully_settled: bool
    created_at: datetime
    updated_at: datetime


class SplitBillSummaryResponse(BaseModel):
    id: int
    title: str
    date: Date
    total_amount: Decimal
    participant_count: int
    paid_participant_count: int
    total_non_payer_count: int
    has_calculation: bool
    is_fully_settled: bool
    settlement_summary: SplitBillSettlementSummaryResponse


class DebtSummaryItem(BaseModel):
    name: str
    subtotal: Decimal


class DebtSummary(BaseModel):
    debtor_name: str
    creditor_name: str
    amount: Decimal
    items: list[DebtSummaryItem]


class SplitBillCalculateResponse(BaseModel):
    title: str
    total_amount: Decimal
    participants: list[SplitBillParticipantResponse]
    debts: list[SplitBillDebtResponse]
    summary: list[DebtSummary]
    text: str


class ReceiptScanItem(BaseModel):
    name: str
    qty: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(gt=Decimal("0"), decimal_places=2)


class ReceiptScanCharge(BaseModel):
    type: str
    name: str
    amount: Decimal = Field(gt=Decimal("0"), decimal_places=2)


class ReceiptScanResponse(BaseModel):
    items: list[ReceiptScanItem] = Field(default_factory=list)
    charges: list[ReceiptScanCharge] = Field(default_factory=list)
