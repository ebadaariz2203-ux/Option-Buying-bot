import os

import requests
from dotenv import load_dotenv

load_dotenv()

# FIX: the bot token and chat ID used to be hardcoded here and committed
# to git -- a live credential sitting in plaintext source, exposed to
# anyone with repo/git-history access. Now read from .env (gitignored),
# same pattern as the Kite credentials. NOTE: the previously-committed
# token is already exposed in git history and should be rotated via
# BotFather regardless of this fix.
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_message(message):

    # FIX: previously called requests.post() unconditionally, and any
    # failure (missing token, network error, bad chat id) would raise
    # and propagate up into the trading loop. Telegram is a
    # notification side-channel -- it should never be able to crash or
    # interrupt a live trading cycle.
    if not BOT_TOKEN or not CHAT_ID:
        print("[TELEGRAM] Skipped: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set in .env")
        return None

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, data=data, timeout=10)
        return response.status_code

    except requests.RequestException as e:
        print(f"[TELEGRAM] Notification failed: {e}")
        return None
