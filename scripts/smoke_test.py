#!/usr/bin/env python3
"""Pre-flight diagnostic for DaycoNet. Run before end-to-end testing."""

import importlib
import os
import sys

_results = []  # list of tuples: (status, name, message)


def record(status: str, name: str, message: str) -> None:
    """Record and print one check result."""
    _results.append((status, name, message))
    print(f"[{status}] {name} - {message}")


def check_python_version() -> bool:
    """Check Python is 3.10 or newer."""
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 10):
        record("OK", "Python version", f"{major}.{minor}")
        return True
    record("FAIL", "Python version", f"{major}.{minor} (need 3.10+)")
    return False


def check_package(module_name: str) -> bool:
    """Try to import a module and report its version."""
    try:
        mod = importlib.import_module(module_name)
        version = getattr(mod, "__version__", "unknown")
        record("OK", f"import {module_name}", version)
        return True
    except Exception as exc:
        record("FAIL", f"import {module_name}", str(exc))
        return False


def check_env(var_name: str) -> bool:
    """Check that an environment variable is set and non-empty."""
    value = os.environ.get(var_name)
    if value and value.strip():
        record("OK", f"env {var_name}", "set")
        return True
    record("FAIL", f"env {var_name}", "not set or empty")
    return False


def check_db_connection(var_name: str, label: str) -> bool:
    """Open a psycopg connection using the DSN in var_name."""
    dsn = os.environ.get(var_name)
    if not dsn:
        record("SKIP", f"DB {label}", f"{var_name} not set")
        return False
    try:
        import psycopg
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
        record("OK", f"DB {label}", version.split(" on ")[0])
        return True
    except Exception as exc:
        record("FAIL", f"DB {label}", str(exc))
        return False


def check_table(dsn: str, table_name: str, expected_columns: list) -> bool:
    """Verify a table exists and has all expected columns."""
    try:
        import psycopg
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
                    (table_name,),
                )
                found = {row[0] for row in cur.fetchall()}
    except Exception as exc:
        record("FAIL", f"table {table_name}", str(exc))
        return False
    if not found:
        record("FAIL", f"table {table_name}", "does not exist")
        return False
    missing = set(expected_columns) - found
    if missing:
        record("FAIL", f"table {table_name}", f"missing columns: {sorted(missing)}")
        return False
    record("OK", f"table {table_name}", f"{len(found)} columns")
    return True


def main() -> int:
    """Run all checks and print summary."""
    print("DaycoNet smoke test")
    print("=" * 60)
    check_python_version()
    for mod in ["psycopg", "psycopg_pool", "psutil", "pydivert", "reportlab", "PySide6"]:
        check_package(mod)
    try:
        importlib.import_module("PySide6.QtCharts")
        record("OK", "import PySide6.QtCharts", "ok")
    except Exception as exc:
        record("WARN", "import PySide6.QtCharts", f"chart tab will show fallback: {exc}")
    check_env("DAYCONET_DSN")
    check_env("DAYCONET_READER_DSN")
    writer_ok = check_db_connection("DAYCONET_DSN", "writer")
    reader_ok = check_db_connection("DAYCONET_READER_DSN", "reader")
    dsn = os.environ.get("DAYCONET_DSN")
    if writer_ok and dsn:
        check_table(dsn, "traffic_raw", ["id", "captured_at", "pid", "process_name", "exe_path", "bytes_sent", "bytes_recv"])
        check_table(dsn, "traffic_hourly", ["bucket_start", "process_name", "bytes_sent", "bytes_recv"])
    else:
        record("SKIP", "table traffic_raw", "writer DB unavailable")
        record("SKIP", "table traffic_hourly", "writer DB unavailable")
    print("=" * 60)
    fails = sum(1 for s, _, _ in _results if s == "FAIL")
    warns = sum(1 for s, _, _ in _results if s == "WARN")
    oks = sum(1 for s, _, _ in _results if s == "OK")
    skips = sum(1 for s, _, _ in _results if s == "SKIP")
    print(f"Summary: {oks} OK, {warns} WARN, {fails} FAIL, {skips} SKIP")
    if fails:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
