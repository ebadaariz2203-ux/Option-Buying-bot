from market_data.kite_provider import KiteProvider


print("\n========== KITE PROVIDER TEST ==========")

try:
    provider = KiteProvider()

    print("\n--- Market Data Test ---")

    market_data = provider.get_market_data()

    print("Data Type     :", type(market_data).__name__)
    print("Total Candles :", len(market_data))

    print("\nColumns:")
    print(market_data.columns.tolist())

    print("\nLatest Candle:")
    print(market_data.tail(1))

    print("\n--- Option Chain Test ---")

    spot_price = 24570.65

    option_chain = provider.get_option_chain(spot_price)

    print("ATM Strike :", option_chain["ATM_Strike"])
    print("IsSimulated:", option_chain["IsSimulated"])

    print("\nOptions:")

    for option in option_chain["Strikes"]:
        print(option)

except Exception as e:

    print("\n[KITE PROVIDER ERROR]")
    print(e)