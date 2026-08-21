import sys
import os

import sys
import os

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from dotenv import load_dotenv
from kiteconnect import KiteConnect


load_dotenv()

API_KEY = os.getenv("KITE_API_KEY")
ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN")

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)


print("\n========== ACTUAL NIFTY CE/PE LTP ==========")

try:
    instruments = [
        "NFO:NIFTY2681124550CE",
        "NFO:NIFTY2681124550PE"
    ]

    data = kite.ltp(instruments)

    for symbol in instruments:
        option = data[symbol]

        print(f"\n{symbol}")
        print("Instrument Token :", option["instrument_token"])
        print("Last Price (LTP) :", option["last_price"])

except Exception as e:
    print("\n[KITE OPTION LTP ERROR]")
    print(e)

# on 1th Aug 12:40 AM added

print("\n========== NIFTY HISTORICAL DATA TEST ==========")

try:
    from datetime import datetime, timedelta

    to_date = datetime.now()
    from_date = to_date - timedelta(days=1)

    candles = kite.historical_data(
        instrument_token=256265,
        from_date=from_date,
        to_date=to_date,
        interval="5minute"
    )

    print("Historical candles:", len(candles))

    if candles:
        print("First candle:", candles[0])
        print("Last candle :", candles[-1])

except Exception as e:
    print("\n[KITE HISTORICAL DATA ERROR]")
    print(type(e).__name__)
    print(e)  

# ==========================================
# NIFTY FUTURES DATA TEST
# ==========================================

print("\n========== NIFTY FUTURES DATA TEST ==========")

try:
    from market_data.kite_provider import KiteProvider

    provider = KiteProvider()

    futures_data = provider.get_nifty_futures_data()

    print("\n========== FUTURES VOLUME CHECK ==========")
    print(futures_data[
        [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]
    ].tail(10))

    print("\nLatest Futures Volume :",
          futures_data["Volume"].iloc[-1])

    print("==========================================")

except Exception as e:

    print("\n[KITE FUTURES DATA ERROR]")
    print(type(e).__name__)
    print(e)      