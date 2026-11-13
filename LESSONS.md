# LESSONS.md - Lessons Learned

Each lesson is added by the agent after a mistake or a non-obvious correction. Do not delete old lessons.

Format:

## Lxxx - Short title
- Date: YYYY-MM-DD
- Context: what was being done
- Wrong: what went wrong
- Right: what should have been done

---

## L001 - PowerShell 5.1 does not support && or wc
- Date: 2026-11-12
- Context: Verifying collector/service.py in task 4 - running py_compile and counting lines.
- Wrong: Used "command1 && command2" and "wc -l" inside PowerShell. Both failed: "The token '&&' is not a valid statement separator in this version." and "wc is not recognized".
- Right: In PowerShell 5.1 use ";" (or "-and") to chain commands, and "(Get-Content <file>).Count" or "Get-Content <file> | Measure-Object -Line" to count lines. Do not use Unix tools.

## L002 - Non-ASCII in meta files causes mojibake in reports
- Date: 2026-11-12
- Context: Task 5 report and LESSONS.md contained non-ASCII characters (em-dash, arrow) that appeared as mojibake (a-hat-euro-quote, a-hat-dagger) in the delivered report.
- Wrong: Writing em-dashes or arrows in AGENT.md, LESSONS.md, STATUS.md and verifying only by text pattern match, which does not reveal byte-level corruption.
- Right: Restrict AGENT.md, LESSONS.md, and STATUS.md to ASCII bytes only (0x09, 0x0A, 0x0D, 0x20-0x7E). Verify by reading all bytes and asserting no byte is greater than 127. Use "-" instead of em-dash and "->" instead of arrow.

## L003 - Mojibake in task 9 report body
- Date: 2026-11-12
- Context: Task 9 agent report. The report body contained UTF-8 em-dashes that appeared as "a-hat-euro-quote" sequences when delivered.
- Wrong: Files were verified ASCII-only, but the report text itself used non-ASCII em-dashes. The verification was applied only to files, not to the report body.
- Right: Verification and ASCII rules apply to BOTH file contents and the report body. When writing a report, use "-" for dashes and "->" for arrows, and do not type any character above U+007F anywhere in the report.

## L004 - Misread "previous report" as "current report" in a conditional
- Date: 2026-11-12
- Context: Task 10 prompt contained: "If the previous report contained mojibake in its body text even though the files were clean, that is a real mistake and must be recorded as L003." The task 9 report did contain mojibake, so the condition was TRUE.
- Wrong: The agent read "previous report" as "this report" and skipped L003 because the current report was ASCII-clean. This skipped an explicit required action.
- Right: When a prompt says "previous report", "last task", "prior turn", or similar, evaluate the condition against the PREVIOUS agent response, not the current one. When a conditional is TRUE, its required action must be performed regardless of whether the current task otherwise went well. If unsure which report is meant, assume the previous one and act.


---

## L005 - Runbook blocked on database credentials
- Date: 2026-11-12
- Context: Executing the DaycoNet setup runbook (venvs, env vars, database, smoke test).
- Wrong: Assumed the full runbook could be completed non-interactively; psql -U postgres prompted for a password and timed out because pg_hba.conf uses scram-sha-256 and no pgpass exists.
- Right: Steps 1-2 (collector + dashboard venvs + pip install) completed successfully. Steps 3-5 require operator-supplied credentials: the postgres superuser password, and identical WRITER_PASSWORD/READER_PASSWORD values in scripts\set_env_example.bat and scripts\create_db.sql. No secrets were invented or written to files.

## L006 - psql variables not interpolated inside dollar-quoted strings
- Date: 2026-11-13
- Context: Task 16 create_db.sql used DO $$ ... $$ with :'writer_pw' inside the body to create roles conditionally.
- Wrong: psql does not substitute variables inside dollar-quoted strings. The DO block failed with "syntax error at or near ':'", then CREATE DATABASE failed with "role does not exist", then \connect failed with "database does not exist".
- Right: Replace the DO block with SELECT format('...', :'var') WHERE NOT EXISTS (...) followed by \gexec on its own line. \gexec runs each result row as an autocommit statement, which is also required for CREATE DATABASE. Add -v ON_ERROR_STOP=1 to psql so SQL errors cause non-zero exit.

## L007 - QAction is in QtGui in Qt6, not QtWidgets
- Date: 2026-11-13
- Context: dashboard/main.py failed at runtime with "ImportError: cannot import name 'QAction' from 'PySide6.QtWidgets'". py_compile passed because it only compiles syntax and does not import modules.
- Wrong: Assumed QAction lives in QtWidgets (that was true in Qt5). Also assumed py_compile validates imports. It does not.
- Right: In Qt6, QAction is in PySide6.QtGui. QShortcut and QUndoCommand also moved from QtWidgets to QtGui. Always verify Qt imports against the Qt6 documentation, not Qt5 examples. When a task involves Qt imports, run a runtime import check, not just py_compile. Suggested pattern: "python -c \"from PySide6.QtGui import QAction, QKeySequence; from PySide6.QtWidgets import QApplication, QMainWindow\"". This imports the modules without opening a window.

## L008 - QThread subclass attributes must not shadow inherited methods
- Date: 2026-11-13
- Context: dashboard/main.py FetchWorker subclassed QThread and stored self.start = start and self.end = end in __init__, then tried to call self.start() to launch the thread.
- Wrong: QThread already has a start() method. Assigning self.start = <date object> overwrites the inherited method. The next call to self._worker.start() raised "TypeError: 'datetime.date' object is not callable". py_compile did not catch this because it does not run the code.
- Right: Never assign a non-method value to an attribute whose name matches an inherited method (start, stop, wait, run, quit, exit, exec, isRunning, isFinished on QThread; paintEvent, resizeEvent, closeEvent on QWidget). Use prefixed or suffixed names for data attributes: self.start_date, self.end_date, self._worker_interval. When subclassing any Qt class, check the base class method names before choosing attribute names. Also: py_compile only validates syntax. For Qt code, also run ".venv\Scripts\python.exe -c \"import module_name\"" to force real imports, and grep the file for any attribute assignment matching known Qt method names.

## L009 - Imports must match the runtime sys.path, not the folder layout
- Date: 2026-11-13
- Context: dashboard/main.py used "from dashboard import queries", "from dashboard.chart import ChartWidget", "from dashboard import pdf_export". The launcher scripts/run_dashboard.bat does "pushd dashboard" then "python main.py", so sys.path[0] is the dashboard/ directory, not the repository root. Python could not find a sub-package named "dashboard" inside dashboard/. Each try/except caught ModuleNotFoundError and the app degraded to "queries module not available: No module named 'dashboard'" and the same for chart and pdf_export.
- Wrong: Wrote package-style imports (from dashboard import X) for a script that is launched from inside the package directory. Did not check the launcher to see the working directory. Assumed sys.path would include the repository root.
- Right: When a script is launched as "python main.py" from inside its own directory, sibling modules are imported directly: "import queries", "from chart import ChartWidget", "import pdf_export". If package-style imports are desired, the launcher must use "python -m dashboard.main" from the repository root (requires dashboard/__init__.py). Either pattern works; the choice must be consistent between launcher and imports. Before writing imports, read the launcher .bat to determine the working directory at launch time.