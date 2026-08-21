import os
from dotenv import load_dotenv
from kiteconnect import KiteConnect

from market_data.kite_provider import KiteProvider

load_dotenv()

print("\n========== KITE MULTI-STRIKE OPTION CHAIN ==========")

try:

    provider = KiteProvider()

    # ------------------------------------------
    # Get NIFTY Spot
    # ------------------------------------------

    spot_data = provider.kite.ltp(["NSE:NIFTY 50"])

    spot_price = spot_data["NSE:NIFTY 50"]["last_price"]

    print("\nNIFTY Spot :", spot_price)

    # ------------------------------------------
    # Get Dynamic Option Chain
    # ------------------------------------------

    option_chain = provider.get_option_chain(spot_price)

    print("\nATM Strike :", option_chain["ATM_Strike"])

    print("\n========== OPTION DATA ==========")

    for option in option_chain["Strikes"]:

        print(
            f"{option['Strike']:7.0f} "
            f"{option['Type']:2} | "
            f"LTP: {option['LTP']:8.2f} | "
            f"OI: {option['OI']:10} | "
            f"Volume: {option['Volume']:12} | "
            f"Bid: {option['Bid']:7.2f} | "
            f"Ask: {option['Ask']:7.2f}"
        )

    print("\nTotal Contracts :", len(option_chain["Strikes"]))

    print("\nIs Simulated    :", option_chain["IsSimulated"])

except Exception as e:

    print("\n[KITE OPTION CHAIN ERROR]")
    print(e)