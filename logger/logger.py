import sys
import os

from loguru import logger


os.makedirs("logs", exist_ok=True)

# FIX: loguru attaches a default handler (id=0) to sys.stderr at import
# time, with level="DEBUG" — this handler completely ignores whatever
# level you set on any NEW handler you add via logger.add(). That's why
# logger.debug(...) calls (e.g. the per-tick trade monitoring lines in
# monitor_open_trade()) were still printing to the console every few
# seconds, even though the file sink below was configured at
# level="INFO". Removing the default handler fixes this.
logger.remove()

# ==========================================
# CONSOLE — only INFO and above.
# Keeps the terminal readable during a live/paper session: routine
# per-tick monitoring (logged as DEBUG) stays out of the console, only
# meaningful events (INFO/WARNING/ERROR) show up.
# ==========================================
# ==========================================
# CONSOLE — only INFO and above.
# Keeps the terminal readable during a live/paper session: routine
# per-tick monitoring (logged as DEBUG) stays out of the console, only
# meaningful events (INFO/WARNING/ERROR) show up.
#
# FIX: uses sys.stdout instead of sys.stderr. PowerShell treats ANY
# stderr output from a native command (like "python main.py") as an
# "error record" when piped with "2>&1 |" -- even harmless INFO log
# lines -- printing noisy "NativeCommandError" wrappers around every
# single logger.info() call. Routing to stdout avoids this entirely
# and captures cleanly with Tee-Object.
# ==========================================
logger.add(
    sys.stdout,
    level="INFO",
    format="{time:HH:mm:ss} | {level} | {message}",
)

# ==========================================
# FILE — full DEBUG detail retained.
# Nothing is lost — every debug line (including per-tick monitoring)
# is still fully captured here for later troubleshooting / the
# post_market_audit.py workflow.
# ==========================================
logger.add(
    "logs/trading_bot.log",
    rotation="10 MB",
    retention="10 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)
