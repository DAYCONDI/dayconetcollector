"""Read-only report queries for the DaycoNet dashboard."""

import logging
import os
from datetime import date
from typing import Optional

from psycopg_pool import ConnectionPool

# Date parameters are passed as date objects. PostgreSQL treats a date compared
# to a timestamptz as midnight of the session timezone.

log = logging.getLogger(__name__)

READER_DSN = os.environ.get("DAYCONET_READER_DSN")

_PERIOD_TRUNC = {
    "hour":  "date_trunc('hour', bucket_start)",
    "day":   "date_trunc('day', bucket_start)",
    "week":  "date_trunc('week', bucket_start)",
    "month": "date_trunc('month', bucket_start)",
    "year":  "date_trunc('year', bucket_start)",
}


def validate_period(period: str) -> str:
    """Return period if it is one of day/week/month/year, else raise ValueError."""
    if period not in _PERIOD_TRUNC:
        raise ValueError(f"Invalid period '{period}'. Expected one of: day, week, month, year.")
    return period


def _configure_readonly(conn) -> None:
    """Force the session to be read-only and clear the transaction."""
    conn.execute("SET SESSION default_transaction_read_only = on")
    conn.commit()


def make_reader_pool(dsn: Optional[str] = None, min_size: int = 1, max_size: int = 2) -> ConnectionPool:
    """Create a read-only connection pool for report queries."""
    if dsn is None:
        dsn = READER_DSN
    if dsn is None or dsn.strip() == "":
        raise ValueError("DAYCONET_READER_DSN is not set.")
    pool = ConnectionPool(
        conninfo=dsn,
        min_size=min_size,
        max_size=max_size,
        timeout=30.0,
        open=False,
        configure=_configure_readonly,
    )
    pool.open(wait=False)
    return pool


def fetch_totals(pool, start: date, end: date) -> dict:
    """Return totals over [start, end). end is exclusive midnight."""
    duration = max(1, int((end - start).total_seconds()))
    sql = """
        SELECT
            COALESCE(SUM(bytes_sent), 0)::bigint AS bytes_sent,
            COALESCE(SUM(bytes_recv), 0)::bigint AS bytes_recv,
            COALESCE(SUM(bytes_sent + bytes_recv), 0)::bigint AS total_bytes,
            COUNT(DISTINCT process_name)::int AS process_count
        FROM traffic_hourly
        WHERE bucket_start >= %s AND bucket_start < %s
    """
    with pool.connection() as conn:
        cur = conn.execute(sql, (start, end))
        columns = [desc[0] for desc in cur.description]
        row = cur.fetchone()
    result = dict(zip(columns, row))
    result["duration_seconds"] = duration
    return result


def fetch_process_breakdown(pool, start: date, end: date, limit: int = 50, duration_seconds: int = 1) -> list[dict]:
    """Return per-process totals in [start, end), ordered by total_bytes desc then process_name asc."""
    if limit < 1:
        raise ValueError("limit must be >= 1.")
    if limit > 1000:
        raise ValueError("limit must be <= 1000.")
    sql = """
        SELECT
            process_name,
            SUM(bytes_sent)::bigint AS bytes_sent,
            SUM(bytes_recv)::bigint AS bytes_recv,
            SUM(bytes_sent + bytes_recv)::bigint AS total_bytes
        FROM traffic_hourly
        WHERE bucket_start >= %s AND bucket_start < %s
        GROUP BY process_name
        ORDER BY total_bytes DESC, process_name ASC
        LIMIT %s
    """
    with pool.connection() as conn:
        cur = conn.execute(sql, (start, end, limit))
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    result = [dict(zip(columns, row)) for row in rows]
    for item in result:
        item["avg_bytes_per_sec"] = int(item["total_bytes"] / max(1, duration_seconds))
    return result


def fetch_time_series(pool, period: str, start: date, end: date) -> list[dict]:
    """Return per-period totals in [start, end), one row per bucket of period."""
    validate_period(period)
    trunc_expr = _PERIOD_TRUNC[period]
    sql = f"""
        SELECT
            {trunc_expr} AS period_start,
            SUM(bytes_sent)::bigint AS bytes_sent,
            SUM(bytes_recv)::bigint AS bytes_recv,
            SUM(bytes_sent + bytes_recv)::bigint AS total_bytes
        FROM traffic_hourly
        WHERE bucket_start >= %s AND bucket_start < %s
        GROUP BY period_start
        ORDER BY period_start ASC
    """
    with pool.connection() as conn:
        cur = conn.execute(sql, (start, end))
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def fetch_top_process_time_series(pool, period: str, start: date, end: date, top_n: int = 5) -> dict:
    """Return per-period time series for the top N processes by total bytes over [start, end)."""
    validate_period(period)
    if top_n < 1:
        raise ValueError("top_n must be >= 1.")
    if top_n > 20:
        raise ValueError("top_n must be <= 20.")
    breakdown = fetch_process_breakdown(pool, start, end, limit=top_n)
    names = [row["process_name"] for row in breakdown]
    if not names:
        return {}
    trunc_expr = _PERIOD_TRUNC[period]
    sql = f"""
        SELECT
            process_name,
            {trunc_expr} AS period_start,
            SUM(bytes_sent)::bigint AS bytes_sent,
            SUM(bytes_recv)::bigint AS bytes_recv,
            SUM(bytes_sent + bytes_recv)::bigint AS total_bytes
        FROM traffic_hourly
        WHERE bucket_start >= %s AND bucket_start < %s
          AND process_name = ANY(%s)
        GROUP BY process_name, period_start
        ORDER BY process_name ASC, period_start ASC
    """
    result = {name: [] for name in names}
    with pool.connection() as conn:
        cur = conn.execute(sql, (start, end, names))
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    for row in rows:
        record = dict(zip(columns, row))
        result[record["process_name"]].append({
            "period_start": record["period_start"],
            "bytes_sent": record["bytes_sent"],
            "bytes_recv": record["bytes_recv"],
            "total_bytes": record["total_bytes"],
        })
    return result
