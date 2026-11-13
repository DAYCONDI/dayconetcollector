@echo off
REM Run the DaycoNet smoke test inside the root .venv.
setlocal

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Root .venv not found. Run scripts\setup_venv.bat first.
    exit /b 1
)

call .venv\Scripts\activate.bat
python scripts\smoke_test.py
set RC=%ERRORLEVEL%
deactivate
exit /b %RC%
