# run_bot.ps1
#
# Launches the trading bot with:
#   1. UTF-8 console encoding (fixes checkmark/emoji crash)
#   2. Full session output captured to logs\session_YYYYMMDD.txt
#      (needed later for post_market_audit.py)
#
# USAGE (from the project root, with your venv already activated):
#   .\run_bot.ps1
#
# If PowerShell blocks running this script the first time, run this
# ONCE in the same terminal, then try again:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Make sure the logs folder exists
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Force UTF-8 console codepage (fixes checkmark/emoji UnicodeEncodeError)
chcp 65001 | Out-Null

# Build today's session log filename
$logFile = "logs\session_$(Get-Date -Format yyyyMMdd).txt"

Write-Host "Starting Option Buying Bot..."
Write-Host "Session will be saved to: $logFile"
Write-Host ""

# Run the bot, capturing all output (console + file) at once
python main.py 2>&1 | Tee-Object -FilePath $logFile
