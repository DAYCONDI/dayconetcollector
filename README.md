# DaycoNet

Per-process internet usage monitor for Windows 10 (64-bit).

## What it does

The collector service runs in the background, independent of the dashboard. It captures per-process network packets with pydivert, attributes them to PIDs, writes raw rows to PostgreSQL every 5 seconds, and aggregates them into hourly buckets. The dashboard is opened on demand whenever you want to view reports. PostgreSQL stores all data. Daily, weekly, monthly, and yearly reports include charts and PDF export.

## Requirements

- Windows 10 64-bit
- Python 3.10 or newer, 64-bit (tested on 3.13), with the venv module available
- PostgreSQL 16 running locally
- Administrator access for the collector and for installing the service
- NSSM 2.24 or newer at C:\Tools\nssm\nssm.exe (only needed for service installation)

## Quick Start

1. Create the root virtualenv and install all dependencies (non-admin PowerShell at the repository root):
   scripts\setup_venv.bat

2. Run the database setup script (same terminal). It prompts for the postgres superuser password, then asks you to choose passwords for dayconet_writer and dayconet_reader. It creates roles, database, tables, indexes, and persists the two environment variables.
   scripts\setup_db.bat
   When it finishes, CLOSE that terminal. The setx command only takes effect in new terminals.

3. Open a NEW terminal (non-admin) at the repository root and run the smoke test:
   scripts\run_smoke_test.bat
   Expect: RESULT: PASS. If any line says [FAIL], see "## If something breaks" below.

4. Two options to run the collector:
   - Manual (foreground, admin PowerShell): scripts\run_collector_manual.bat
   - As a service (admin PowerShell):
       scripts\build_exe.bat
       scripts\install_service.bat

5. Open the dashboard (non-admin, anytime):
   scripts\run_dashboard.bat

6. Optional cleanup: after verifying that scripts\run_smoke_test.bat passes, you may delete collector\.venv and dashboard\.venv; they are no longer used.

## If something breaks

**[FAIL] env ... not set** - Run scripts\setup_db.bat (or scripts\set_env_example.bat for env vars only), then close and reopen the terminal.

**[FAIL] DB writer / DB reader** - Confirm PostgreSQL is running (services.msc -> postgresql-x64-16). Confirm the passwords you entered in scripts\setup_db.bat match the roles created by it.

**[FAIL] import pydivert** - Open PowerShell as Administrator. pydivert requires elevation.

**Service will not start** - Check logs\collector_out.log and logs\collector_err.log. Run scripts\uninstall_service.bat then scripts\install_service.bat to reinstall with fresh paths.

## Environment variables

| Name | Used by | Purpose |
|------|---------|---------|
| DAYCONET_DSN | collector | Full connection string to PostgreSQL as user dayconet_writer. |
| DAYCONET_READER_DSN | dashboard | Full connection string to PostgreSQL as user dayconet_reader (read-only). |

Both variables are set by scripts\setup_db.bat during database setup. Use scripts\set_env_example.bat only as the manual alternative for updating environment variables without touching the database. The dashboard only reads; the collector only writes.

## Project structure

```
dayconet/
  collector/        service.py, db.py, config.py
  dashboard/        main.py, queries.py, chart.py, pdf_export.py
  db/               schema.sql
  scripts/          create_db.sql, setup_db.bat, setup_venv.bat, build_exe.bat,
                    install_service.bat, uninstall_service.bat,
                    run_collector_manual.bat, run_dashboard.bat,
                    run_smoke_test.bat, set_env_example.bat, smoke_test.py
  logs/             collector.log, collector_out.log, collector_err.log (created at runtime)
  requirements.txt
  AGENT.md, LESSONS.md, STATUS.md, README.md, .gitignore, .gitattributes
```

## Architecture

**Collector service**: runs in the background, captures packets with pydivert, attributes them to PIDs, writes raw rows every 5 seconds, aggregates into hourly buckets every 60 seconds, prunes raw rows older than 30 days.

**Storage**: PostgreSQL 16 with two tables (traffic_raw, traffic_hourly) and three indexes.

**Dashboard**: PySide6 + QtCharts, read-only connection, four tabs (Daily, Weekly, Monthly, Yearly), each with a totals header, a top-process table, a line chart, and an Export PDF button.

The collector and dashboard are independent processes. Closing the dashboard does not stop collection.

## Status and roadmap

See STATUS.md for the current task and next steps. See LESSONS.md for recorded agent lessons.

## License

TBD
