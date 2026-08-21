import os
from datetime import date

from dotenv import load_dotenv
from kiteconnect import KiteConnect

load_dotenv()

API_KEY = os.getenv("KITE_API_KEY")
ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN")

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

STRIKE_STEP = 50

print("\n========== KITE OPTION QUOTE TEST ==========")

try:

    # ==========================================
    # 1. NIFTY SPOT
    # ==========================================

    spot_data = kite.ltp(["NSE:NIFTY 50"])
    spot_price = spot_data["NSE:NIFTY 50"]["last_price"]

    print("\nNIFTY Spot :", spot_price)

    # ==========================================
    # 2. ATM STRIKE
    # ==========================================

    atm_strike = round(spot_price / STRIKE_STEP) * STRIKE_STEP

    print("ATM Strike :", atm_strike)

    # ==========================================
    # 3. NFO INSTRUMENTS
    # ==========================================

    instruments = kite.instruments("NFO")

    nifty_options = [
        instrument
        for instrument in instruments
        if instrument["name"] == "NIFTY"
        and instrument["instrument_type"] in ("CE", "PE")
        and instrument["expiry"] >= date.today()
    ]

    # ==========================================
    # 4. NEAREST EXPIRY
    # ==========================================

    expiries = sorted(
        set(
            instrument["expiry"]
            for instrument in nifty_options
        )
    )

    nearest_expiry = expiries[0]

    print("Expiry      :", nearest_expiry)

    # ==========================================
    # 5. ATM CE / PE
    # ==========================================

    atm_options = [
        instrument
        for instrument in nifty_options
        if instrument["strike"] == atm_strike
        and instrument["expiry"] == nearest_expiry
    ]

    symbols = [
        f"NFO:{instrument['tradingsymbol']}"
        for instrument in atm_options
    ]

    print("\nSymbols:")

    for symbol in symbols:
        print(symbol)

    # ==========================================
    # 6. RAW QUOTE DATA
    # ==========================================

    print("\n========== RAW QUOTE ==========")

    quote_data = kite.quote(symbols)

    for symbol in symbols:

        quote = quote_data[symbol]

        print("\n--------------------------------")
        print("Symbol :", symbol)

        print("LTP    :", quote["last_price"])
        print("OI     :", quote["oi"])
        print("Volume :", quote["volume"])

        print("Bid    :", quote["depth"]["buy"][0]["price"])
        print("Ask    :", quote["depth"]["sell"][0]["price"])

        print("\nFull Quote:")
        print(quote)

except Exception as e:

    print("\n[KITE OPTION QUOTE ERROR]")
    print(e)