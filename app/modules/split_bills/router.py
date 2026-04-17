from typing import Tuple

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.split_bills.dependencies import (
    get_owned_bill,
    get_bill_debt,
)
from app.modules.split_bills.gemini_client import (
    is_available as gemini_is_available,
    parse_receipt,
)
from app.modules.split_bills.models import SplitBill, SplitBillDebt
from app.modules.split_bills.schemas import (
    ReceiptScanResponse,
    SplitBillCalculateRequest,
    SplitBillCalculateResponse,
    SplitBillCreate,
    SplitBillDetailResponse,
    SplitBillResponse,
    SplitBillSummaryResponse,
    SplitBillSettlementInput,
    SplitBillSettlementResponse,
)
from app.modules.split_bills.service import (
    calculate_split,
    create_bill,
    create_settlement,
    get_bill_detail,
    get_bills_by_user,
    get_bill_summaries_by_user,
    soft_delete_bill,
)

_SCAN_ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
_SCAN_MAX_BYTES = 5 * 1024 * 1024

router = APIRouter(prefix="/v1/split-bills", tags=["Split Bills"])


@router.post(
    "",
    response_model=SplitBillResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_split_bill(
    data: SplitBillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        bill = await create_bill(db, current_user.id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return bill


@router.get("", response_model=list[SplitBillResponse])
async def list_bills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_bills_by_user(db, current_user.id)


@router.get("/summary", response_model=list[SplitBillSummaryResponse])
async def list_bill_summaries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_bill_summaries_by_user(db, current_user.id)


@router.get("/{bill_id}", response_model=SplitBillDetailResponse)
async def bill_detail(
    bill: SplitBill = Depends(get_owned_bill),
    db: AsyncSession = Depends(get_db),
):
    return await get_bill_detail(db, bill)


@router.post(
    "/{bill_id}/calculate",
    response_model=SplitBillCalculateResponse,
)
async def calculate(
    data: SplitBillCalculateRequest,
    bill: SplitBill = Depends(get_owned_bill),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await calculate_split(db, bill, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return result


@router.post(
    "/{bill_id}/debts/{debt_id}/settle",
    response_model=SplitBillSettlementResponse,
)
async def settle_debt(
    data: SplitBillSettlementInput,
    context: Tuple[SplitBill, SplitBillDebt] = Depends(get_bill_debt),
    db: AsyncSession = Depends(get_db),
):
    bill, debt = context
    try:
        settlement = await create_settlement(db, bill, debt, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return settlement


@router.delete("/{bill_id}", status_code=status.HTTP_200_OK)
async def delete_bill(
    bill: SplitBill = Depends(get_owned_bill),
    db: AsyncSession = Depends(get_db),
):
    await soft_delete_bill(db, bill)
    return {"message": "Bill deleted successfully"}


@router.post("/scan-receipt", response_model=ReceiptScanResponse)
async def scan_receipt(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not gemini_is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Receipt scanning is not configured on the server",
        )

    mime_type = (image.content_type or "").lower()
    if mime_type not in _SCAN_ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, or WEBP images are supported",
        )

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )
    if len(image_bytes) > _SCAN_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image exceeds 5 MB limit",
        )

    normalized_mime = "image/jpeg" if mime_type == "image/jpg" else mime_type

    try:
        result = await parse_receipt(image_bytes, normalized_mime)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to scan receipt: {e}",
        )

    return result
