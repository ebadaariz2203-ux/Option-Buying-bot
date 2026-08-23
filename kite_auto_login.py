"""
Semi-automated Kite (Zerodha) login helper.

What it does automatically:
- Opens the Kite login URL in your default browser
- Waits for you to paste the `request_token` from the redirected URL
- Generates the access_token
- Saves KITE_ACCESS_TOKEN directly into your .env file (no manual copy-paste needed)

What you still do manually (required by Zerodha's OAuth flow, cannot be skipped):
- Log in with your Zerodha username/password/TOTP in the browser
- Copy the `request_token` value from the redirected URL's query string

Run this once every trading day before starting the bot:
    python kite_auto_login.py
"""

import os
import re
import webbrowser
from kiteconnect import KiteConnect
from dotenv import load_dotenv, set_key

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

load_dotenv(ENV_PATH)

API_KEY = os.getenv("KITE_API_KEY")
API_SECRET = os.getenv("KITE_API_SECRET")

if not API_KEY or not API_SECRET:
    print("\n[ERROR] KITE_API_KEY or KITE_API_SECRET missing in .env file.")
    exit(1)

kite = KiteConnect(api_key=API_KEY)
login_url = kite.login_url()

print("\n========== KITE LOGIN ==========")
print("Opening login page in your browser...")
print(f"If it doesn't open automatically, visit:\n{login_url}\n")
webbrowser.open(login_url)

print("After logging in, you'll be redirected to a URL like:")
print("  https://your-redirect-url/?request_token=XXXXXXXX&action=login&status=success\n")

raw_input_value = input("Paste the FULL redirected URL OR just the request_token: ").strip()

# Allow user to paste either the full URL or just the token
match = re.search(r"request_token=([^&]+)", raw_input_value)
request_token = match.group(1) if match else raw_input_value

try:
    session = kite.generate_session(request_token, api_secret=API_SECRET)
    access_token = session["access_token"]

    set_key(ENV_PATH, "KITE_ACCESS_TOKEN", access_token)

    print("\n========== KITE SESSION ==========")
    print("Login successful ✅")
    print("Access token generated and saved to .env automatically.")
    print("You can now run the bot normally (main.py / run_bot.bat).")

except Exception as e:
    print("\n[KITE SESSION ERROR]")
    print(e)
