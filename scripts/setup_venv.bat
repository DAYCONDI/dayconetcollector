@echo off
REM Create the DaycoNet root virtualenv and install all dependencies.
REM Run once from the repository root. Does not require Administrator.
setlocal

if not exist "requirements.txt" (
    echo [ERROR] Run this script from the repository root: requirements.txt not found.
    exit /b 1
)

if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Reusing existing .venv
) else (
    echo Creating .venv with system Python...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] python -m venv failed.
        exit /b 1
    )
)

call .venv\Scripts\activate.bat
echo.
echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] pip upgrade failed.
    exit /b 1
)

echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed.
    exit /b 1
)

echo.
echo [OK] Root .venv ready.
echo.
echo NEXT STEPS:
echo   1. Verify by running: scripts\run_smoke_test.bat
echo   2. You may delete collector\.venv and dashboard\.venv manually after verification.
endlocal
