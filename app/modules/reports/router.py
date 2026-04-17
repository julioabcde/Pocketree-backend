from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.accounts.models import Account
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.reports.schemas import (
    AccountBreakdownResponse,
    CashflowTrendItem,
    CategoryBreakdownResponse,
    OverviewResponse,
    PeriodComparisonResponse,
    ReportGroupBy,
    TopTransactionItem,
)
from app.modules.reports.service import (
    get_account_breakdown,
    get_cashflow_trend,
    get_category_breakdown,
    get_overview,
    get_period_comparison,
    get_top_transactions,
)
from app.modules.reports.utils import validate_date_range
from app.modules.transactions.models import TransactionType

router = APIRouter(prefix="/v1/reports", tags=["Reports"])


def _validate_common_params(
    start_date: date,
    end_date: date,
) -> None:
    try:
        validate_date_range(start_date, end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


async def _validate_account_ownership(
    account_id: int,
    user_id: int,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(Account.id).where(
            Account.id == account_id,
            Account.user_id == user_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Account not found")


@router.get("/overview", response_model=OverviewResponse)
async def overview(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    account_id: int | None = Query(default=None, description="Filter by account"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate_common_params(start_date, end_date)
    if account_id is not None:
        await _validate_account_ownership(account_id, current_user.id, db)

    return await get_overview(
        db,
        current_user.id,
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
    )


@router.get("/cashflow-trend", response_model=list[CashflowTrendItem])
async def cashflow_trend(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    account_id: int | None = Query(default=None, description="Filter by account"),
    group_by: ReportGroupBy = Query(default=ReportGroupBy.day),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate_common_params(start_date, end_date)
    if account_id is not None:
        await _validate_account_ownership(account_id, current_user.id, db)

    try:
        return await get_cashflow_trend(
            db,
            current_user.id,
            start_date=start_date,
            end_date=end_date,
            account_id=account_id,
            group_by=group_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/category-breakdown", response_model=CategoryBreakdownResponse)
async def category_breakdown(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    account_id: int | None = Query(default=None, description="Filter by account"),
    type: TransactionType = Query(default=TransactionType.expense),
    top_n: int = Query(default=10, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate_common_params(start_date, end_date)
    if account_id is not None:
        await _validate_account_ownership(account_id, current_user.id, db)

    return await get_category_breakdown(
        db,
        current_user.id,
        start_date=start_date,
        end_date=end_date,
        transaction_type=type,
        top_n=top_n,
        account_id=account_id,
    )


@router.get("/account-breakdown", response_model=AccountBreakdownResponse)
async def account_breakdown(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    account_id: int | None = Query(default=None, description="Filter by account"),
    type: TransactionType = Query(default=TransactionType.expense),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate_common_params(start_date, end_date)
    if account_id is not None:
        await _validate_account_ownership(account_id, current_user.id, db)

    return await get_account_breakdown(
        db,
        current_user.id,
        start_date=start_date,
        end_date=end_date,
        transaction_type=type,
        account_id=account_id,
    )


@router.get("/top-transactions", response_model=list[TopTransactionItem])
async def top_transactions(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    account_id: int | None = Query(default=None, description="Filter by account"),
    type: TransactionType = Query(default=TransactionType.expense),
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate_common_params(start_date, end_date)
    if account_id is not None:
        await _validate_account_ownership(account_id, current_user.id, db)

    return await get_top_transactions(
        db,
        current_user.id,
        start_date=start_date,
        end_date=end_date,
        transaction_type=type,
        limit=limit,
        account_id=account_id,
    )


@router.get("/period-comparison", response_model=PeriodComparisonResponse)
async def period_comparison(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    account_id: int | None = Query(default=None, description="Filter by account"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate_common_params(start_date, end_date)
    if account_id is not None:
        await _validate_account_ownership(account_id, current_user.id, db)

    return await get_period_comparison(
        db,
        current_user.id,
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
    )
