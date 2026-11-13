@echo off
REM Set persistent environment variables for DaycoNet.
REM Edit the four placeholders below, then run this file once.
REM You must open a NEW terminal for the variables to take effect.
setlocal

set WRITER_PASSWORD=CHANGE_ME_WRITER
set READER_PASSWORD=CHANGE_ME_READER
set PG_HOST=localhost
set PG_PORT=5432

setx DAYCONET_DSN "host=%PG_HOST% port=%PG_PORT% dbname=dayconet user=dayconet_writer password=%WRITER_PASSWORD%"
setx DAYCONET_READER_DSN "host=%PG_HOST% port=%PG_PORT% dbname=dayconet user=dayconet_reader password=%READER_PASSWORD%"

echo.
echo [OK] Environment variables set.
echo Close this terminal and open a new one for changes to take effect.
endlocal
