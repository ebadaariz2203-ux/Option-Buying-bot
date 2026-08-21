from datetime import datetime, time
from zoneinfo import ZoneInfo


def is_market_open():

    ist = ZoneInfo("Asia/Kolkata")
    now = datetime.now(ist)

    # Saturday = 5, Sunday = 6
    if now.weekday() >= 5:
        print("Market Closed (Weekend)")
        return False          # FIX: was returning True (bug) - bot thought
                               # weekend market was OPEN and tried to fetch
                               # data, likely crashing the run loop.

    market_open = time(9, 15)
    market_close = time(15, 30)

    current_time = now.time()

    if market_open <= current_time <= market_close:
        return True

    print("Market Closed (Outside Trading Hours)")
    return False
