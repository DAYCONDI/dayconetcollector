"""Runtime configuration for the Dayconet collector.

All values are pure module-level constants. Importing this module performs no
side effects: no directories are created, no files are opened or read, and no
network connections are made.
"""

import os
from pathlib import Path

# Repository root: collector/ lives one level below it.
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"

# Tunables (override via environment where supported by the consuming layer).
DB_DSN = os.environ.get("DAYCONET_DSN")  # may be None; DB layer validates
SAMPLE_INTERVAL_SEC = 5
AGGREGATE_INTERVAL_SEC = 60
RAW_RETENTION_DAYS = 30
LOG_LEVEL = os.environ.get("DAYCONET_LOG_LEVEL", "INFO").upper()
