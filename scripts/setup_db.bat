@echo off
REM DaycoNet database setup. Prompts for passwords, creates roles and tables,
REM and persists environment variables via setx.
REM Run from the repository root. Does not require Administrator.
setlocal EnableDelayedExpansion

if not exist "db\schema.sql" (
    echo [ERROR] Run this script from the repository root.
    exit /b 1
)

if not exist "scripts\create_db.sql" (
    echo [ERROR] scripts\create_db.sql not found.
    exit /b 1
)

echo.
echo DaycoNet database setup
echo ========================
echo This script will:
echo   1. Create PostgreSQL roles dayconet_writer and dayconet_reader
echo   2. Create database dayconet
echo   3. Create tables and indexes
echo   4. Persist DAYCONET_DSN and DAYCONET_READER_DSN for the current user
echo.
echo Note: passwords are echoed as you type and stored in HKCU\Environment.
echo       Use simple alphanumeric passwords (no ^& ^| ^< ^> ^^ ^" or %% characters).
echo.

set /p PG_HOST=PostgreSQL host [localhost]:
if "%PG_HOST%"=="" set PG_HOST=localhost

set /p PG_PORT=PostgreSQL port [5432]:
if "%PG_PORT%"=="" set PG_PORT=5432

set /p PG_SUPER_PW=Postgres superuser password:
if "%PG_SUPER_PW%"=="" (echo [ERROR] Postgres password is empty. & exit /b 1)

set /p WRITER_PW=New password for dayconet_writer:
if "%WRITER_PW%"=="" (echo [ERROR] Writer password is empty. & exit /b 1)

set /p READER_PW=New password for dayconet_reader:
if "%READER_PW%"=="" (echo [ERROR] Reader password is empty. & exit /b 1)

set PGPASSWORD=%PG_SUPER_PW%

echo.
echo Step 1/2: creating roles and database...
psql -h %PG_HOST% -p %PG_PORT% -U postgres -v ON_ERROR_STOP=1 -v writer_pw="%WRITER_PW%" -v reader_pw="%READER_PW%" -f scripts\create_db.sql
if errorlevel 1 (
    echo [ERROR] create_db.sql failed. See messages above.
    set PGPASSWORD=
    exit /b 1
)

echo.
echo Step 2/2: creating tables, indexes, and grants...
psql -h %PG_HOST% -p %PG_PORT% -U postgres -v ON_ERROR_STOP=1 -d dayconet -f db\schema.sql
if errorlevel 1 (
    echo [ERROR] schema.sql failed. See messages above.
    set PGPASSWORD=
    exit /b 1
)

set PGPASSWORD=

echo.
echo Persisting environment variables for the current Windows user...
setx DAYCONET_DSN "host=%PG_HOST% port=%PG_PORT% dbname=dayconet user=dayconet_writer password=%WRITER_PW%"
if errorlevel 1 (
    echo [ERROR] setx for DAYCONET_DSN failed.
    exit /b 1
)
setx DAYCONET_READER_DSN "host=%PG_HOST% port=%PG_PORT% dbname=dayconet user=dayconet_reader password=%READER_PW%"
if errorlevel 1 (
    echo [ERROR] setx for DAYCONET_READER_DSN failed.
    exit /b 1
)

echo.
echo [OK] Database setup complete.
echo.
echo NEXT STEPS:
echo   1. Close this terminal.
echo   2. Open a NEW terminal at the repository root.
echo   3. Run: python scripts\smoke_test.py
echo      Expect: RESULT: PASS
endlocal
