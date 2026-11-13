@echo off
REM Run the collector in the foreground for testing.
REM Must be run as Administrator (pydivert needs it).
REM Press Ctrl+C to stop.
setlocal

if not exist "collector\service.py" (
    echo [ERROR] Run this script from the repository root.
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Root .venv not found. Run scripts\setup_venv.bat first.
    exit /b 1
)

if "%DAYCONET_DSN%"=="" (
    echo [ERROR] DAYCONET_DSN is not set.
    echo Run scripts\setup_db.bat first, then open a NEW terminal.
    exit /b 1
)

call .venv\Scripts\activate.bat
pushd collector
python service.py
popd
endlocal
