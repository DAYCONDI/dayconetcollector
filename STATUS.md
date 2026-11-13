# STATUS.md - Project Status

Updated by the agent after every task.

## Current

- project complete and pushed to GitHub

## Completed
- scaffold initialization (task 1) - done
- config + schema + requirements (task 2) - done
- collector/db.py (pool + retry + insert + aggregate/prune) - done
- collector/service.py (packet loop + flush + aggregate threads) - done
- AGENT.md hardened (PowerShell 5.1 rules + strict error recording) - done
- LESSONS.md L001 recorded - done
- ASCII-only enforcement on meta files + AGENT.md rule + L002 - done
- dashboard/main.py skeleton (PySide6 QMainWindow with 4 tabs) - done
- dashboard/requirements.txt - done
- dashboard/queries.py (read-only report queries) - done
- dashboard/main.py wired to queries.py (worker thread, totals header, top-process table) - done
- dashboard/queries.py added "hour" to _PERIOD_TRUNC - done
- LESSONS.md L003 and L004 recorded - done
- AGENT.md conditionals section + report-body ASCII rule - done
- dashboard/chart.py grab_png method - done
- dashboard/pdf_export.py (reportlab A4 report) - done
- dashboard/main.py Export PDF wired to active tab - done
- scripts/ boilerplate (create_db.sql, build_exe.bat, install_service.bat, uninstall_service.bat, run_collector_manual.bat, run_dashboard.bat, set_env_example.bat) - done
- scripts/smoke_test.py (environment diagnostic) - done
- README.md rewritten to match final project state - done
- setup runbook steps 1-2 (collector + dashboard venvs + pip install) - done
- SQL grant bugs fixed (order + DELETE grant) - done
- scripts/setup_db.bat (single-command DB setup with prompts) - done
- README Quick Start updated to use setup_db.bat - done
- create_db.sql fixed (DO replaced with \gexec; variables now interpolated outside dollar quotes) - done
- setup_db.bat psql calls now use ON_ERROR_STOP=1 - done
- Consolidated to single root .venv (merged requirements.txt, setup_venv.bat, run_smoke_test.bat) - done
- All run scripts updated to use root .venv - done
- collector/requirements.txt and dashboard/requirements.txt removed - done
- Security audit completed - see task 19 report
- Fixed QAction import for PySide6 6.x (moved to QtGui) - done
- L007 recorded about py_compile not catching import errors - done
- Collector diagnostic logging improved (port map size, buffer pids, cumulative flushed, LOG_LEVEL from env) - done
- Fixed QThread.start shadowing in FetchWorker (renamed to start_date/end_date) - done
- L008 recorded about Qt base-class method shadowing - done
- Fixed module imports in dashboard/main.py (local imports because launcher runs from dashboard/) - done
- L009 recorded about import style vs runtime sys.path - done
- dashboard/queries.py duration_seconds + avg_bytes_per_sec added - done
- dashboard/chart.py BarChartWidget + PieChartWidget added - done
- dashboard/pdf_export.py duration_seconds + Speed column added - done
- dashboard/main.py Speed column, Bar+Pie charts, chart selector, dark UI, PDF updates - done
- Fixed unknown process names via name_cache resolved at packet time - done
- collector/DaycoNetCollector.spec created - done
- scripts/build_exe.bat now uses spec file - done
- scripts/install_service.bat hardened - done
- dashboard/DaycoNetDashboard.spec created - done
- scripts/build_dashboard_exe.bat created - done
- .gitignore updated to track custom .spec files - done
- Final documentation update and GitHub push - done
## Next

- none - project is feature-complete

## Blocked
- none
