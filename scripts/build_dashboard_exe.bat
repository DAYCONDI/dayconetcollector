@echo off
REM Build DaycoNetDashboard.exe with PyInstaller using a spec file.
REM Run from the repository root.
setlocal

if not exist "dashboard\main.py" (
    echo [ERROR] Run this script from the repository root: dashboard\main.py not found.
    exit /b 1
)

if not exist "dashboard\DaycoNetDashboard.spec" (
    echo [ERROR] dashboard\DaycoNetDashboard.spec not found.
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Root .venv not found. Run scripts\setup_venv.bat first.
    exit /b 1
)

call .venv\Scripts\activate.bat
pip install pyinstaller

pushd dashboard
pyinstaller --clean --noconfirm DaycoNetDashboard.spec
set RC=%ERRORLEVEL%
popd

if not "%RC%"=="0" (
    echo [ERROR] PyInstaller failed with exit code %RC%.
    exit /b 1
)

if not exist "dashboard\dist\DaycoNetDashboard.exe" (
    echo [ERROR] Build succeeded but dashboard\dist\DaycoNetDashboard.exe not found.
    exit /b 1
)

echo.
echo [OK] Built: dashboard\dist\DaycoNetDashboard.exe
echo You can now double-click this exe to open the dashboard without Python.
endlocal
