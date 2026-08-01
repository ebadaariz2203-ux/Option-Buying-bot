from datetime import datetime


def save_order_history(order):

    order["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n========== ORDER HISTORY ==========")
    print(f"Order ID : {order['OrderID']}")
    print(f"Signal   : {order['Signal']}")
    print(f"Status   : {order['Status']}")
    print(f"Time     : {order['Timestamp']}")
    print("===================================")