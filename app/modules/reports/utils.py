import hashlib
import json
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any

from sqlalchemy import case, func

from app.modules.transactions.models import Transaction


def validate_date_range(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise ValueError("'start_date' must be on or before 'end_date'")


def enforce_group_by_limit(
    group_by: str,
    start_date: date,
    end_date: date,
) -> None:
    total_days = (end_date - start_date).days + 1

    if group_by == "day" and total_days > 90:
        raise ValueError("Date range exceeds limit for group_by='day' (max 90 days)")

    if group_by == "week" and total_days > 365:
        raise ValueError(
            "Date range exceeds limit for group_by='week' (max 365 days)"
        )


def round_decimal(value: Decimal | int | float | str, places: int = 2) -> Decimal:
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    quantum = Decimal("1").scaleb(-places)
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def calculate_percentage_sql(amount_expr, total_expr):
    denominator = func.nullif(total_expr, 0)
    return case(
        (
            denominator.isnot(None),
            func.round((amount_expr * Decimal("100.00")) / denominator, 2),
        ),
        else_=None,
    )


def build_base_query(query, user_id: int, account_id: int | None = None):
    query = query.where(
        Transaction.user_id == user_id,
        ~Transaction.is_deleted,
        Transaction.transfer_id.is_(None),
    )

    if account_id is not None:
        query = query.where(Transaction.account_id == account_id)

    return query


def _start_of_week(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _start_of_month(value: date) -> date:
    return value.replace(day=1)


def _next_month_start(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def generate_time_buckets(
    start_date: date,
    end_date: date,
    group_by: str,
) -> list[dict[str, Any]]:
    if group_by == "day":
        cursor = start_date
    elif group_by == "week":
        cursor = _start_of_week(start_date)
    else:
        cursor = _start_of_month(start_date)

    buckets: list[dict[str, Any]] = []

    while cursor <= end_date:
        if group_by == "day":
            natural_end = cursor
            period = cursor.isoformat()
            next_cursor = cursor + timedelta(days=1)
        elif group_by == "week":
            natural_end = cursor + timedelta(days=6)
            iso_year, iso_week, _ = cursor.isocalendar()
            period = f"{iso_year}-W{iso_week:02d}"
            next_cursor = cursor + timedelta(days=7)
        else:
            next_cursor = _next_month_start(cursor)
            natural_end = next_cursor - timedelta(days=1)
            period = cursor.strftime("%Y-%m")

        bucket_start = max(cursor, start_date)
        bucket_end = min(natural_end, end_date)

        if bucket_start <= bucket_end:
            buckets.append(
                {
                    "key": cursor,
                    "period": period,
                    "start_date": bucket_start,
                    "end_date": bucket_end,
                }
            )

        cursor = next_cursor

    return buckets


def zero_fill_series(
    grouped_rows: dict[date, dict[str, Decimal]],
    buckets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    cumulative_net = Decimal("0.00")

    for bucket in buckets:
        row = grouped_rows.get(bucket["key"], {})
        income = row.get("income", Decimal("0.00"))
        expense = row.get("expense", Decimal("0.00"))
        net = income - expense
        cumulative_net += net

        results.append(
            {
                "period": bucket["period"],
                "start_date": bucket["start_date"],
                "end_date": bucket["end_date"],
                "income": income,
                "expense": expense,
                "net": net,
                "cumulative_net": cumulative_net,
            }
        )

    return results


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        return {key: _normalize_value(value[key]) for key in sorted(value)}

    if isinstance(value, list):
        return [_normalize_value(item) for item in value]

    return value


def normalize_query_params_with_defaults(
    params: dict[str, Any],
    defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    merged = dict(defaults or {})
    merged.update(params)
    return {key: _normalize_value(merged[key]) for key in sorted(merged)}


def build_cache_key(
    endpoint: str,
    user_id: int,
    normalized_params: dict[str, Any],
) -> str:
    payload = json.dumps(
        normalized_params,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"reports:{endpoint}:{user_id}:{digest}"
