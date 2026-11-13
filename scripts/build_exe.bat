@echo off
REM Build DaycoNetCollector.exe with PyInstaller using a spec file.
REM Run from the repository root.
setlocal

if not exist "collector\service.py" (
    echo [ERROR] Run this script from the repository root: collector\service.py not found.
    exit /b 1
)

if not exist "collector\DaycoNetCollector.spec" (
    echo [ERROR] collector\DaycoNetCollector.spec not found.
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Root .venv not found. Run scripts\setup_venv.bat first.
    exit /b 1
)

call .venv\Scripts\activate.bat
pip install pyinstaller

pushd collector
pyinstaller --clean --noconfirm DaycoNetCollector.spec
set RC=%ERRORLEVEL%
popd

if not "%RC%"=="0" (
    echo [ERROR] PyInstaller failed with exit code %RC%.
    exit /b 1
)

if not exist "collector\dist\DaycoNetCollector.exe" (
    echo [ERROR] Build succeeded but collector\dist\DaycoNetCollector.exe not found.
    exit /b 1
)

echo.
echo [OK] Built: collector\dist\DaycoNetCollector.exe
echo.
echo NEXT STEPS:
echo   1. Verify the exe runs by double-clicking it as Administrator.
echo   2. Run scripts\install_service.bat to install it as a Windows service.
endlocal
