from datetime import datetime
from zoneinfo import ZoneInfo


def save_order_history(order):

    # FIX: was naive datetime.now() (whatever timezone the host OS
    # happens to be set to), inconsistent with the IST-aware timestamps
    # recorded elsewhere (e.g. trade_history.py's ExitTime, core/bot.py's
    # session-time logic all use ZoneInfo("Asia/Kolkata")). On a non-IST
    # host this could record an order timestamp that doesn't line up
    # with the rest of the trade's IST-aware timeline.
    order["Timestamp"] = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%Y-%m-%d %H:%M:%S")

    print("\n========== ORDER HISTORY ==========")
    print(f"Order ID : {order['OrderID']}")
    print(f"Signal   : {order['Signal']}")
    print(f"Status   : {order['Status']}")
    print(f"Time     : {order['Timestamp']}")
    print("===================================")