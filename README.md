# DaycoNet

Per-process internet usage monitor for Windows.

## Overview

DaycoNet is a Windows 10 (64-bit) Python project that monitors per-process network usage. A background Windows service collects per-process send and receive byte counts via pydivert and stores the samples in a local PostgreSQL 16 database. The data is aggregated hourly into summary tables. A separate PySide6 + QtCharts dashboard, opened on demand, shows daily, weekly, monthly, and yearly reports with charts and PDF export. The collector and dashboard are independent: closing the dashboard does not stop data collection.

## Architecture

- Collector Service: pydivert + psycopg, runs as a Windows service.
- Storage: PostgreSQL 16 with raw sample tables and hourly aggregated tables.
- Dashboard: PySide6 + QtCharts with PDF export.

## Prerequisites

- Windows 10 64-bit
- Python 3.10+ 64-bit
- PostgreSQL 16 running locally
- Administrator access
- NSSM 2.24+ for service installation

## Project Structure

```
collector/
dashboard/
db/
scripts/
logs/
.gitignore
.gitattributes
AGENT.md
LESSONS.md
STATUS.md
README.md
```

## Setup

1. Create the database and users in PostgreSQL.
2. Apply db/schema.sql to create the raw and hourly tables.
3. Create a virtual environment and install collector/requirements.txt.
4. Set the DAYCONET_DSN environment variable.

## Running

Install the collector as a Windows service via NSSM (see scripts/). The dashboard is run separately when needed.

## License

TBD
