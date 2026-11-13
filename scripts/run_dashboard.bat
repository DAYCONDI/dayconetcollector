@echo off
REM Run the DaycoNet dashboard GUI from the root venv.
setlocal

if not exist "dashboard\main.py" (
    echo [ERROR] Run this script from the repository root.
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Root .venv not found. Run scripts\setup_venv.bat first.
    exit /b 1
)

if "%DAYCONET_READER_DSN%"=="" (
    echo [WARN] DAYCONET_READER_DSN is not set. The dashboard will open but will show
    echo        "Error: DAYCONET_READER_DSN is not set." in each tab.
    echo        Run scripts\setup_db.bat first, then open a NEW terminal.
    echo.
    pause
)

call .venv\Scripts\activate.bat
pushd dashboard
python main.py
popd
endlocal
