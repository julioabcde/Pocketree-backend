import json
from datetime import date, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import Date, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.accounts.models import Account
from app.modules.category.models import Category
from app.modules.reports.schemas import (
    AccountBreakdownItem,
    AccountBreakdownResponse,
    CashflowTrendItem,
    CategoryBreakdownItem,
    CategoryBreakdownResponse,
    CountDelta,
    MetricDelta,
    OverviewDelta,
    OverviewPeriod,
    OverviewResponse,
    PeriodComparisonDelta,
    PeriodComparisonPeriod,
    PeriodComparisonResponse,
    ReportGroupBy,
    TopTransactionItem,
)
from app.modules.reports.utils import (
    build_base_query,
    build_cache_key,
    calculate_percentage_sql,
    enforce_group_by_limit,
    generate_time_buckets,
    normalize_query_params_with_defaults,
    round_decimal,
    validate_date_range,
    zero_fill_series,
)
from app.modules.transactions.models import Transaction, TransactionType

try:
    from redis.asyncio import Redis
except ImportError: 
    Redis = None 


__all__ = [
    "get_overview",
    "get_cashflow_trend",
    "get_category_breakdown",
    "get_account_breakdown",
    "get_top_transactions",
    "get_period_comparison",
    "invalidate_reports_cache",
    "close_redis_client",
]

ZERO = Decimal("0.00")

_redis_client = None


async def _get_redis_client():
    global _redis_client

    if not settings.reports_cache_enabled:
        return None

    if not settings.redis_url:
        logger.warning("REPORTS_CACHE_ENABLED is true but REDIS_URL is empty")
        return None

    if Redis is None:
        logger.warning("Redis package is not installed, cache is disabled")
        return None

    if _redis_client is not None:
        return _redis_client

    try:
        _redis_client = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await _redis_client.ping()
        return _redis_client
    except Exception as exc: 
        logger.warning(f"Failed to initialize Redis cache: {exc}")
        _redis_client = None
        return None


async def _cache_get(key: str) -> dict | list | None:
    client = await _get_redis_client()
    if client is None:
        return None

    try:
        payload = await client.get(key)
    except Exception as exc: 
        logger.warning(f"Cache read failed for key '{key}': {exc}")
        return None

    if payload is None:
        return None

    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


async def _cache_set(key: str, data: dict | list, ttl_seconds: int) -> None:
    client = await _get_redis_client()
    if client is None:
        return

    try:
        await client.set(key, json.dumps(data, separators=(",", ":")), ex=ttl_seconds)
    except Exception as exc: 
        logger.warning(f"Cache write failed for key '{key}': {exc}")


def _income_sum_expr():
    return func.coalesce(
        func.sum(
            case(
                (Transaction.type == TransactionType.income, Transaction.amount),
                else_=ZERO,
            )
        ),
        ZERO,
    )


def _expense_sum_expr():
    return func.coalesce(
        func.sum(
            case(
                (Transaction.type == TransactionType.expense, Transaction.amount),
                else_=ZERO,
            )
        ),
        ZERO,
    )


async def _period_totals(
    db: AsyncSession,
    user_id: int,
    start_date: date,
    end_date: date,
    account_id: int | None,
) -> PeriodComparisonPeriod:
    query = (
        select(
            _income_sum_expr().label("income"),
            _expense_sum_expr().label("expense"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .select_from(Transaction)
        .where(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
        )
    )
    query = build_base_query(query, user_id, account_id)

    row = (await db.execute(query)).one()

    income = row.income or ZERO
    expense = row.expense or ZERO
    transaction_count = row.transaction_count or 0

    return PeriodComparisonPeriod(
        income=income,
        expense=expense,
        net=income - expense,
        transaction_count=transaction_count,
    )


def _metric_delta(current: Decimal, previous: Decimal) -> MetricDelta:
    amount = current - previous
    percent = None
    if previous != 0:
        percent = round_decimal((amount / previous) * Decimal("100"), 2)

    return MetricDelta(
        amount=amount,
        percent=percent,
    )


def _count_delta(current: int, previous: int) -> CountDelta:
    amount = current - previous
    percent = None

    if previous != 0:
        percent = round_decimal((Decimal(amount) / Decimal(previous)) * Decimal("100"), 2)

    return CountDelta(
        amount=amount,
        percent=percent,
    )


def _period_range(
    start_date: date,
    end_date: date,
) -> tuple[date, date]:
    duration_days = (end_date - start_date).days + 1
    previous_end = start_date - timedelta(days=1)
    previous_start = previous_end - timedelta(days=duration_days - 1)
    return previous_start, previous_end


async def get_overview(
    db: AsyncSession,
    user_id: int,
    start_date: date,
    end_date: date,
    account_id: int | None = None,
) -> OverviewResponse:
    validate_date_range(start_date, end_date)

    normalized = normalize_query_params_with_defaults(
        params={
            "start_date": start_date,
            "end_date": end_date,
            "account_id": account_id,
        },
        defaults={
            "account_id": None,
        },
    )
    cache_key = build_cache_key("overview", user_id, normalized)

    cached = await _cache_get(cache_key)
    if cached is not None:
        return OverviewResponse.model_validate(cached)

    current = await _period_totals(
        db,
        user_id,
        start_date,
        end_date,
        account_id,
    )

    prev_start, prev_end = _period_range(start_date, end_date)
    previous = await _period_totals(
        db,
        user_id,
        prev_start,
        prev_end,
        account_id,
    )

    savings_rate = None
    if current.income != 0:
        savings_rate = round_decimal((current.net / current.income) * Decimal("100"), 2)

    response = OverviewResponse(
        total_income=current.income,
        total_expense=current.expense,
        net=current.net,
        transaction_count=current.transaction_count,
        savings_rate=savings_rate,
        previous_period=OverviewPeriod(
            income=previous.income,
            expense=previous.expense,
            net=previous.net,
        ),
        delta=OverviewDelta(
            income=_metric_delta(current.income, previous.income),
            expense=_metric_delta(current.expense, previous.expense),
            net=_metric_delta(current.net, previous.net),
        ),
    )

    await _cache_set(
        cache_key,
        response.model_dump(mode="json"),
        settings.reports_cache_ttl_overview,
    )

    return response


def _period_start_expression(group_by: ReportGroupBy):
    if group_by == ReportGroupBy.day:
        return Transaction.date
    if group_by == ReportGroupBy.week:
        return cast(func.date_trunc("week", Transaction.date), Date)
    return cast(func.date_trunc("month", Transaction.date), Date)


async def get_cashflow_trend(
    db: AsyncSession,
    user_id: int,
    start_date: date,
    end_date: date,
    group_by: ReportGroupBy = ReportGroupBy.day,
    account_id: int | None = None,
) -> list[CashflowTrendItem]:
    validate_date_range(start_date, end_date)
    enforce_group_by_limit(group_by.value, start_date, end_date)

    normalized = normalize_query_params_with_defaults(
        params={
            "start_date": start_date,
            "end_date": end_date,
            "account_id": account_id,
            "group_by": group_by,
        },
        defaults={
            "account_id": None,
            "group_by": ReportGroupBy.day,
        },
    )
    cache_key = build_cache_key("cashflow-trend", user_id, normalized)

    cached = await _cache_get(cache_key)
    if cached is not None:
        return [CashflowTrendItem.model_validate(item) for item in cached]

    period_start = _period_start_expression(group_by)

    query = (
        select(
            period_start.label("period_start"),
            _income_sum_expr().label("income"),
            _expense_sum_expr().label("expense"),
        )
        .select_from(Transaction)
        .where(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
        )
        .group_by(period_start)
        .order_by(period_start)
    )
    query = build_base_query(query, user_id, account_id)

    rows = (await db.execute(query)).all()

    row_map = {
        row.period_start: {
            "income": row.income or ZERO,
            "expense": row.expense or ZERO,
        }
        for row in rows
    }

    buckets = generate_time_buckets(start_date, end_date, group_by.value)
    serialized = zero_fill_series(row_map, buckets)
    items = [CashflowTrendItem.model_validate(item) for item in serialized]

    await _cache_set(
        cache_key,
        [item.model_dump(mode="json") for item in items],
        settings.reports_cache_ttl_trend,
    )

    return items


async def get_category_breakdown(
    db: AsyncSession,
    user_id: int,
    start_date: date,
    end_date: date,
    transaction_type: TransactionType,
    top_n: int = 10,
    account_id: int | None = None,
) -> CategoryBreakdownResponse:
    validate_date_range(start_date, end_date)

    normalized = normalize_query_params_with_defaults(
        params={
            "start_date": start_date,
            "end_date": end_date,
            "account_id": account_id,
            "type": transaction_type,
            "top_n": top_n,
        },
        defaults={
            "account_id": None,
            "type": TransactionType.expense,
            "top_n": 10,
        },
    )
    cache_key = build_cache_key("category-breakdown", user_id, normalized)

    cached = await _cache_get(cache_key)
    if cached is not None:
        return CategoryBreakdownResponse.model_validate(cached)

    grouped_query = (
        select(
            Transaction.category_id.label("category_id"),
            func.coalesce(Category.name, "Uncategorized").label("name"),
            func.coalesce(Category.color, "#808080").label("color"),
            func.coalesce(Category.icon, "").label("icon"),
            func.coalesce(func.sum(Transaction.amount), ZERO).label("amount"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .select_from(Transaction)
        .outerjoin(Category, Category.id == Transaction.category_id)
        .where(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.type == transaction_type,
        )
        .group_by(
            Transaction.category_id,
            Category.name,
            Category.color,
            Category.icon,
        )
    )
    grouped_query = build_base_query(grouped_query, user_id, account_id)

    grouped = grouped_query.subquery()

    total_amount = func.sum(grouped.c.amount).over()
    percentage = calculate_percentage_sql(grouped.c.amount, total_amount)

    query = (
        select(
            grouped.c.category_id,
            grouped.c.name,
            grouped.c.color,
            grouped.c.icon,
            grouped.c.amount,
            grouped.c.transaction_count,
            percentage.label("percentage"),
            total_amount.label("total_amount"),
        )
        .order_by(
            grouped.c.amount.desc(),
            grouped.c.transaction_count.desc(),
            grouped.c.name.asc(),
        )
        .limit(top_n)
    )

    rows = (await db.execute(query)).all()

    response = CategoryBreakdownResponse(
        total_amount=(rows[0].total_amount if rows else ZERO) or ZERO,
        items=[
            CategoryBreakdownItem(
                category_id=row.category_id,
                name=row.name,
                color=row.color,
                icon=row.icon,
                amount=row.amount,
                percentage=row.percentage,
                transaction_count=row.transaction_count,
            )
            for row in rows
        ],
    )

    await _cache_set(
        cache_key,
        response.model_dump(mode="json"),
        settings.reports_cache_ttl_breakdown,
    )

    return response


async def get_account_breakdown(
    db: AsyncSession,
    user_id: int,
    start_date: date,
    end_date: date,
    transaction_type: TransactionType,
    account_id: int | None = None,
) -> AccountBreakdownResponse:
    validate_date_range(start_date, end_date)

    normalized = normalize_query_params_with_defaults(
        params={
            "start_date": start_date,
            "end_date": end_date,
            "account_id": account_id,
            "type": transaction_type,
        },
        defaults={
            "account_id": None,
            "type": TransactionType.expense,
        },
    )
    cache_key = build_cache_key("account-breakdown", user_id, normalized)

    cached = await _cache_get(cache_key)
    if cached is not None:
        return AccountBreakdownResponse.model_validate(cached)

    grouped_query = (
        select(
            Account.id.label("account_id"),
            Account.name.label("account_name"),
            Account.type.label("account_type"),
            func.coalesce(func.sum(Transaction.amount), ZERO).label("amount"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .select_from(Transaction)
        .join(Account, Account.id == Transaction.account_id)
        .where(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.type == transaction_type,
        )
        .group_by(Account.id, Account.name, Account.type)
    )
    grouped_query = build_base_query(grouped_query, user_id, account_id)

    grouped = grouped_query.subquery()

    total_amount_expr = func.sum(grouped.c.amount).over()
    percentage = calculate_percentage_sql(grouped.c.amount, total_amount_expr)

    query = select(
        grouped.c.account_id,
        grouped.c.account_name,
        grouped.c.account_type,
        grouped.c.amount,
        grouped.c.transaction_count,
        percentage.label("percentage"),
        total_amount_expr.label("total_amount"),
    ).order_by(grouped.c.amount.desc(), grouped.c.transaction_count.desc())

    rows = (await db.execute(query)).all()

    response = AccountBreakdownResponse(
        total_amount=rows[0].total_amount if rows else ZERO,
        items=[
            AccountBreakdownItem(
                account_id=row.account_id,
                account_name=row.account_name,
                account_type=row.account_type,
                amount=row.amount,
                percentage=row.percentage,
                transaction_count=row.transaction_count,
            )
            for row in rows
        ],
    )

    await _cache_set(
        cache_key,
        response.model_dump(mode="json"),
        settings.reports_cache_ttl_breakdown,
    )

    return response


async def get_top_transactions(
    db: AsyncSession,
    user_id: int,
    start_date: date,
    end_date: date,
    transaction_type: TransactionType,
    limit: int = 5,
    account_id: int | None = None,
) -> list[TopTransactionItem]:
    validate_date_range(start_date, end_date)

    normalized = normalize_query_params_with_defaults(
        params={
            "start_date": start_date,
            "end_date": end_date,
            "account_id": account_id,
            "type": transaction_type,
            "limit": limit,
        },
        defaults={
            "account_id": None,
            "type": TransactionType.expense,
            "limit": 5,
        },
    )
    cache_key = build_cache_key("top-transactions", user_id, normalized)

    cached = await _cache_get(cache_key)
    if cached is not None:
        return [TopTransactionItem.model_validate(item) for item in cached]

    query = (
        select(
            Transaction.id.label("transaction_id"),
            Transaction.date,
            Transaction.amount,
            Account.name.label("account"),
            func.coalesce(Category.name, "Uncategorized").label("category"),
            Transaction.note,
        )
        .select_from(Transaction)
        .join(Account, Account.id == Transaction.account_id)
        .outerjoin(Category, Category.id == Transaction.category_id)
        .where(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.type == transaction_type,
        )
        .order_by(
            Transaction.amount.desc(),
            Transaction.date.desc(),
            Transaction.created_at.desc(),
        )
        .limit(limit)
    )
    query = build_base_query(query, user_id, account_id)

    rows = (await db.execute(query)).all()
    items = [
        TopTransactionItem(
            transaction_id=row.transaction_id,
            date=row.date,
            amount=row.amount,
            account=row.account,
            category=row.category,
            note=row.note,
        )
        for row in rows
    ]

    await _cache_set(
        cache_key,
        [item.model_dump(mode="json") for item in items],
        settings.reports_cache_ttl_top_transactions,
    )

    return items


async def get_period_comparison(
    db: AsyncSession,
    user_id: int,
    start_date: date,
    end_date: date,
    account_id: int | None = None,
) -> PeriodComparisonResponse:
    validate_date_range(start_date, end_date)

    normalized = normalize_query_params_with_defaults(
        params={
            "start_date": start_date,
            "end_date": end_date,
            "account_id": account_id,
        },
        defaults={
            "account_id": None,
        },
    )
    cache_key = build_cache_key("period-comparison", user_id, normalized)

    cached = await _cache_get(cache_key)
    if cached is not None:
        return PeriodComparisonResponse.model_validate(cached)

    current = await _period_totals(
        db,
        user_id,
        start_date,
        end_date,
        account_id,
    )

    prev_start, prev_end = _period_range(start_date, end_date)
    previous = await _period_totals(
        db,
        user_id,
        prev_start,
        prev_end,
        account_id,
    )

    response = PeriodComparisonResponse(
        current_period=current,
        previous_period=previous,
        delta=PeriodComparisonDelta(
            income=_metric_delta(current.income, previous.income),
            expense=_metric_delta(current.expense, previous.expense),
            net=_metric_delta(current.net, previous.net),
            transaction_count=_count_delta(
                current.transaction_count,
                previous.transaction_count,
            ),
        ),
    )

    await _cache_set(
        cache_key,
        response.model_dump(mode="json"),
        settings.reports_cache_ttl_period_comparison,
    )

    return response


async def invalidate_reports_cache(user_id: int) -> None:
    client = await _get_redis_client()
    if client is None:
        return

    pattern = f"reports:*:{user_id}:*"
    try:
        cursor = 0
        keys_to_delete: list[str] = []
        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            keys_to_delete.extend(keys)
            if cursor == 0:
                break
        if keys_to_delete:
            await client.unlink(*keys_to_delete)
    except Exception as exc: 
        logger.warning(f"Cache invalidation failed for user {user_id}: {exc}")


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception as exc:  
            logger.warning(f"Error closing Redis client: {exc}")
        finally:
            _redis_client = None
