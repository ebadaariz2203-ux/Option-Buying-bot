@echo off
setlocal

REM Always run relative to this script's own folder, regardless of
REM where it's launched from (double-click, shortcut, etc.)
cd /d "%~dp0"

REM Activate the virtual environment
call .venv\Scripts\activate.bat

REM Make sure the logs folder exists
if not exist logs mkdir logs

REM Build today's date-stamped log filename (YYYYMMDD)
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set DATESTAMP=%%i

set LOGFILE=logs\session_%DATESTAMP%.txt

echo Starting Option Buying Bot...
echo Session will be saved to: %LOGFILE%
echo.

REM Run via an inline PowerShell -Command (not a .ps1 script file),
REM which is NOT subject to the script-file execution policy
REM restriction that blocks .ps1 files. Sets UTF-8 codepage and
REM captures the full session with Tee-Object in one go.
REM NOTE: Tee-Object writes UTF-16 by default on Windows PowerShell 5.1
REM (the -Encoding parameter isn't supported on this version, so we
REM don't force UTF-8 here). This is fine -- post_market_audit.py
REM auto-detects the file's encoding when reading it.
powershell -NoProfile -ExecutionPolicy Bypass -Command "chcp 65001 | Out-Null; python main.py 2>&1 | Tee-Object -FilePath '%LOGFILE%'"

echo.
echo Bot session ended. Press any key to close this window...
pause >nul

endlocal
