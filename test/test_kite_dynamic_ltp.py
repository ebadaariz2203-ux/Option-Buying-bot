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

print("\n========== DYNAMIC NIFTY OPTION LTP ==========")

try:
    # 1. NIFTY Spot
    spot_data = kite.ltp(["NSE:NIFTY 50"])
    spot_price = spot_data["NSE:NIFTY 50"]["last_price"]

    print("\nNIFTY Spot :", spot_price)

    # 2. ATM Strike
    atm_strike = round(spot_price / STRIKE_STEP) * STRIKE_STEP

    print("ATM Strike :", atm_strike)

    # 3. Get NFO instruments
    instruments = kite.instruments("NFO")

    # 4. Current/future NIFTY options
    nifty_options = [
        instrument
        for instrument in instruments
        if instrument["name"] == "NIFTY"
        and instrument["instrument_type"] in ["CE", "PE"]
        and instrument["expiry"] >= date.today()
    ]

    # 5. Find nearest expiry
    expiries = sorted(
        set(instrument["expiry"] for instrument in nifty_options)
    )

    current_expiry = expiries[0]

    print("Expiry      :", current_expiry)

    # 6. Find ATM CE and PE
    atm_options = [
        instrument
        for instrument in nifty_options
        if instrument["expiry"] == current_expiry
        and instrument["strike"] == atm_strike
    ]

    option_symbols = {}

    for instrument in atm_options:
        option_type = instrument["instrument_type"]

        option_symbols[option_type] = (
            "NFO:" + instrument["tradingsymbol"]
        )

    ce_symbol = option_symbols.get("CE")
    pe_symbol = option_symbols.get("PE")

    print("\nCE Symbol   :", ce_symbol)
    print("PE Symbol   :", pe_symbol)

    # 7. Fetch actual LTP
    ltp_data = kite.ltp([ce_symbol, pe_symbol])

    print("\n========== ACTUAL LTP ==========")

    print("CE LTP      :", ltp_data[ce_symbol]["last_price"])
    print("PE LTP      :", ltp_data[pe_symbol]["last_price"])

except Exception as e:
    print("\n[KITE DYNAMIC LTP ERROR]")
    print(e)