@echo off
REM Install DaycoNetCollector as a Windows service via NSSM.
REM Must be run as Administrator.
setlocal

set NSSM=C:\Tools\nssm\nssm.exe
set SERVICE_NAME=DaycoNetCollector
set ROOT=%~dp0..
set EXE_PATH=%ROOT%\collector\dist\DaycoNetCollector.exe
set APP_DIR=%ROOT%\collector
set LOG_DIR=%ROOT%\logs

if not exist "%NSSM%" (
    echo [ERROR] nssm.exe not found at %NSSM%
    echo Download NSSM from https://nssm.cc/ and place nssm.exe at that path.
    exit /b 1
)

if not exist "%EXE_PATH%" (
    echo [ERROR] %EXE_PATH% not found.
    echo Run scripts\build_exe.bat first.
    exit /b 1
)

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

sc query "%SERVICE_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Service %SERVICE_NAME% already exists. Removing it first...
    "%NSSM%" stop %SERVICE_NAME% >nul 2>&1
    "%NSSM%" remove %SERVICE_NAME% confirm >nul 2>&1
    timeout /t 2 /nobreak >nul
)

"%NSSM%" install %SERVICE_NAME% "%EXE_PATH%"
if errorlevel 1 (
    echo [ERROR] NSSM install failed.
    exit /b 1
)

"%NSSM%" set %SERVICE_NAME% AppDirectory "%APP_DIR%"
"%NSSM%" set %SERVICE_NAME% Start SERVICE_AUTO_START
"%NSSM%" set %SERVICE_NAME% Description "DaycoNet Internet Usage Collector"
"%NSSM%" set %SERVICE_NAME% AppStdout "%LOG_DIR%\collector_out.log"
"%NSSM%" set %SERVICE_NAME% AppStderr "%LOG_DIR%\collector_err.log"
"%NSSM%" set %SERVICE_NAME% AppRotateFiles 1
"%NSSM%" set %SERVICE_NAME% AppRotateBytes 10485760
"%NSSM%" set %SERVICE_NAME% AppStopMethodSkip 0
"%NSSM%" set %SERVICE_NAME% AppStopMethodConsole 5000
"%NSSM%" set %SERVICE_NAME% AppThrottle 5000

echo.
echo Starting service...
"%NSSM%" start %SERVICE_NAME%
timeout /t 3 /nobreak >nul
"%NSSM%" status %SERVICE_NAME%

echo.
echo [OK] Service installed and started.
echo.
echo Check logs\collector_out.log and logs\collector_err.log for output.
echo To stop: "%NSSM%" stop %SERVICE_NAME%
echo To remove: scripts\uninstall_service.bat
endlocal
