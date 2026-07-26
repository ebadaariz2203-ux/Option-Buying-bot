from datetime import datetime, time
from zoneinfo import ZoneInfo


def is_market_open():

    ist = ZoneInfo("Asia/Kolkata")
    now = datetime.now(ist)

    # Saturday = 5, Sunday = 6
    if now.weekday() >= 5:
        print("Market Closed (Weekend)")
        return True

    market_open = time(9, 15)
    market_close = time(15, 30)

    current_time = now.time()

    if market_open <= current_time <= market_close:
        return True

    print("Market Closed (Outside Trading Hours)")
    return False