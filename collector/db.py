"""Database access layer for the DaycoNet collector."""

import logging
import time
from typing import Optional

from psycopg_pool import ConnectionPool

log = logging.getLogger(__name__)


def make_pool(dsn: Optional[str], min_size: int = 1, max_size: int = 4) -> ConnectionPool:
    """Create and open (lazily) a connection pool from a DSN."""
    if dsn is None or not dsn.strip():
        raise ValueError("DAYCONET_DSN is not set.")
    pool = ConnectionPool(
        conninfo=dsn,
        min_size=min_size,
        max_size=max_size,
        timeout=30.0,
        open=False,
    )
    pool.open(wait=False)
    return pool


def wait_for_db(pool: ConnectionPool, max_retries: int = 60, delay: float = 5.0) -> None:
    """Wait until PostgreSQL accepts a trivial query on the pool."""
    for attempt in range(1, max_retries + 1):
        try:
            with pool.connection(timeout=5.0) as conn:
                conn.execute("SELECT 1")
        except Exception as exc:
            log.warning("DB not ready (attempt %d/%d): %s", attempt, max_retries, exc)
            time.sleep(delay)
            continue
        log.info("Database is ready (attempt %d).", attempt)
        return
    raise RuntimeError(f"Could not connect to PostgreSQL after {max_retries} attempts.")


def insert_traffic_batch(pool: ConnectionPool, rows: list[tuple]) -> int:
    """Insert a batch of raw traffic rows; return the number of rows inserted."""
    if not rows:
        return 0
    sql = (
        "INSERT INTO traffic_raw (pid, process_name, exe_path, bytes_sent, bytes_recv) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, rows)
    return len(rows)


def aggregate_and_prune(pool: ConnectionPool, retention_days: int) -> tuple[int, int]:
    """Aggregate completed hours into traffic_hourly and prune old raw rows."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO traffic_hourly (bucket_start, process_name, bytes_sent, bytes_recv)
                SELECT
                    date_trunc('hour', captured_at) AS bucket_start,
                    process_name,
                    SUM(bytes_sent) AS bytes_sent,
                    SUM(bytes_recv) AS bytes_recv
                FROM traffic_raw
                WHERE captured_at < date_trunc('hour', now())
                  AND date_trunc('hour', captured_at) NOT IN (SELECT bucket_start FROM traffic_hourly)
                GROUP BY bucket_start, process_name
                ON CONFLICT (bucket_start, process_name) DO NOTHING
                """
            )
            aggregated = cur.rowcount
            cur.execute(
                "DELETE FROM traffic_raw WHERE captured_at < now() - make_interval(days => %s)",
                (retention_days,),
            )
            pruned = cur.rowcount
    return (aggregated, pruned)
