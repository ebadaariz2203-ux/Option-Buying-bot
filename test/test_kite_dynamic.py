import os

from dotenv import load_dotenv
from kiteconnect import KiteConnect

load_dotenv()

API_KEY = os.getenv("KITE_API_KEY")
ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN")

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

print("\n========== KITE NIFTY SPOT ==========")

try:
    data = kite.ltp(["NSE:NIFTY 50"])

    nifty = data["NSE:NIFTY 50"]

    print("Instrument Token :", nifty["instrument_token"])
    print("NIFTY Spot       :", nifty["last_price"])

except Exception as e:
    print("\n[KITE NIFTY ERROR]")
    print(e)