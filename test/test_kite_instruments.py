import os
from dotenv import load_dotenv
from kiteconnect import KiteConnect

load_dotenv()

API_KEY = os.getenv("KITE_API_KEY")
ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN")

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

print("\n========== NIFTY OPTION INSTRUMENTS ==========")

try:
    instruments = kite.instruments("NFO")

    print("Total NFO instruments:", len(instruments))

    nifty_options = [
        instrument
        for instrument in instruments
        if instrument["name"] == "NIFTY"
        and instrument["instrument_type"] in ["CE", "PE"]
    ]

    print("Total NIFTY options:", len(nifty_options))

    print("\n========== SAMPLE NIFTY OPTIONS ==========")

    for instrument in nifty_options[:10]:
        print(
            instrument["tradingsymbol"],
            "| Expiry:", instrument["expiry"],
            "| Strike:", instrument["strike"],
            "| Type:", instrument["instrument_type"],
            "| Token:", instrument["instrument_token"]
        )

except Exception as e:
    print("\n[KITE INSTRUMENT ERROR]")
    print(e)