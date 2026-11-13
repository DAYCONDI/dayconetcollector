@echo off
REM Stop and remove the DaycoNetCollector service via NSSM.
REM Must be run as Administrator.
setlocal

set NSSM=C:\Tools\nssm\nssm.exe
set SERVICE_NAME=DaycoNetCollector

if not exist "%NSSM%" (
    echo [ERROR] nssm.exe not found at %NSSM%
    exit /b 1
)

sc query "%SERVICE_NAME%" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Service %SERVICE_NAME% is not installed.
    exit /b 0
)

echo Stopping service...
"%NSSM%" stop %SERVICE_NAME%
timeout /t 2 /nobreak >nul

echo Removing service...
"%NSSM%" remove %SERVICE_NAME% confirm

echo.
echo [OK] Service removed.
endlocal
