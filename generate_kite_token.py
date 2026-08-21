import os
from dotenv import load_dotenv
from kiteconnect import KiteConnect

load_dotenv()

API_KEY = os.getenv("KITE_API_KEY")
API_SECRET = os.getenv("KITE_API_SECRET")

REQUEST_TOKEN = input("Enter Request Token: ").strip()

kite = KiteConnect(api_key=API_KEY)

try:
    session = kite.generate_session(
        REQUEST_TOKEN,
        api_secret=API_SECRET
    )

    access_token = session["access_token"]

    print("\n========== KITE SESSION ==========")
    print("Login successful ✅")
    print("Access Token generated successfully.")
    print("Access Token:", access_token)

except Exception as e:
    print("\n[KITE SESSION ERROR]")
    print(e)