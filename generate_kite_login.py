from kiteconnect import KiteConnect
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("KITE_API_KEY")

kite = KiteConnect(api_key=API_KEY)

print("\n========== KITE LOGIN ==========")
print("Open this URL in your browser:\n")
print(kite.login_url())