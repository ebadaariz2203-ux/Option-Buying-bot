import sys

# FIX: When stdout is redirected/piped (e.g. via PowerShell's
# Tee-Object, or "python main.py > file.txt"), Windows makes Python
# fall back to the system codepage (cp1252) for stdout instead of
# UTF-8. Several print statements in this codebase use non-ASCII
# characters (checkmarks in feature_manager.py, checkmark/cross emoji
# in bot.py's Target Hit / Stop Loss messages) which cp1252 cannot
# encode -- crashing the whole bot with UnicodeEncodeError the moment
# one of those lines is reached.
#
# Forcing UTF-8 here, as early as possible (before any other imports
# that might print), fixes this for every such line in the codebase
# at once, rather than needing to patch each print statement
# individually.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from config.settings import *
from core.bot import TradingBot


def main():

    print("=" * 50)
    print(BOT_NAME)
    print("Version :", VERSION)
    print("Paper Trading :", PAPER_TRADING)
    print("=" * 50)

    bot = TradingBot()
    bot.run_continuously()


if __name__ == "__main__":
    main()
