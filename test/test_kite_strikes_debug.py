from market_data.kite_provider import KiteProvider

print("\n========== KITE STRIKE DEBUG ==========")

try:
    provider = KiteProvider()

    # NIFTY spot
    spot_data = provider.kite.ltp(["NSE:NIFTY 50"])
    spot_price = spot_data["NSE:NIFTY 50"]["last_price"]

    print("\nNIFTY Spot :", spot_price)

    # Same ATM calculation
    atm_strike = min(
        instrument["strike"]
        for instrument in provider.kite.instruments("NFO")
        if instrument["name"] == "NIFTY"
    )

    # Correct nearest ATM
    instruments = provider.kite.instruments("NFO")

    nifty_options = [
        instrument
        for instrument in instruments
        if instrument["name"] == "NIFTY"
        and instrument["instrument_type"] in ("CE", "PE")
    ]

    atm_strike = min(
        [instrument["strike"] for instrument in nifty_options],
        key=lambda strike: abs(strike - spot_price)
    )

    target_strikes = [
        atm_strike - 100,
        atm_strike - 50,
        atm_strike,
        atm_strike + 50,
        atm_strike + 100,
    ]

    print("\nATM Strike :", atm_strike)

    print("\nTarget Strikes:")
    for strike in target_strikes:
        print(strike)

    print("\n========== MATCHING INSTRUMENTS ==========")

    matches = [
        instrument
        for instrument in nifty_options
        if instrument["strike"] in target_strikes
    ]

    for instrument in matches:
        print(
            instrument["tradingsymbol"],
            "| Strike:", instrument["strike"],
            "| Type:", instrument["instrument_type"],
            "| Expiry:", instrument["expiry"]
        )

    print("\nTotal Matching Instruments :", len(matches))

except Exception as e:
    print("\n[KITE STRIKE DEBUG ERROR]")
    print(e)