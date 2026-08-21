from market_data.kite_provider import KiteProvider
from strategy.strike_selector import select_best_strike


print("\n========== MAIN BOT STRIKE FLOW TEST ==========")

try:

    # ==========================================
    # KITE PROVIDER
    # ==========================================

    provider = KiteProvider()

    # ==========================================
    # NIFTY SPOT
    # ==========================================

    spot_data = provider.kite.ltp(["NSE:NIFTY 50"])
    spot_price = spot_data["NSE:NIFTY 50"]["last_price"]

    print("\nNIFTY Spot :", spot_price)

    # ==========================================
    # REAL KITE OPTION CHAIN
    # ==========================================

    option_chain = provider.get_option_chain(spot_price)

    print("\nATM Strike :", option_chain["ATM_Strike"])

    print("\n========== REAL OPTION CHAIN ==========")

    for option in option_chain["Strikes"]:

        print(
            f"{option['Strike']} {option['Type']} | "
            f"LTP: {option['LTP']} | "
            f"OI: {option['OI']} | "
            f"Volume: {option['Volume']}"
        )

    print("=======================================")

    # ==========================================
    # BUY CALL TEST
    # ==========================================

    call_selected = select_best_strike(
        "BUY CALL",
        option_chain
    )

    print("\n========== BUY CALL ==========")

    if call_selected:

        print("Selected Strike :", call_selected["Strike"])
        print("Type            :", call_selected["Type"])
        print("LTP             :", call_selected["LTP"])
        print("OI              :", call_selected["OI"])
        print("Volume          :", call_selected["Volume"])

    else:
        print("No CE Strike Selected")

    # ==========================================
    # BUY PUT TEST
    # ==========================================

    put_selected = select_best_strike(
        "BUY PUT",
        option_chain
    )

    print("\n========== BUY PUT ==========")

    if put_selected:

        print("Selected Strike :", put_selected["Strike"])
        print("Type            :", put_selected["Type"])
        print("LTP             :", put_selected["LTP"])
        print("OI              :", put_selected["OI"])
        print("Volume          :", put_selected["Volume"])

    else:
        print("No PE Strike Selected")

    print("\n========== TEST COMPLETE ==========")

except Exception as e:

    print("\n[KITE STRIKE FLOW ERROR]")
    print(e)