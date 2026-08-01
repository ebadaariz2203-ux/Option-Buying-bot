from portfolio.portfolio_manager import (
    lock_capital,
    unlock_capital,
    update_balance,
)
from datetime import datetime
import csv
import os


def execute_paper_trade(signal, trade):
    trade_value = trade["Entry"] * trade["Quantity"]
    if not lock_capital(trade_value):

        print("Insufficient Balance")

        return None

    trade_data = {
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Signal": signal,
        "Entry": trade["Entry"],
        "StopLoss": trade["StopLoss"],
        "Target": trade["Target"],
        "Status": "OPEN"
    }
    return trade_data


def save_trade(trade_data):

    file_name = "trade_history/trade_history.csv"
    file_exists = os.path.isfile(file_name)

    with open(file_name, mode="a", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "Time",
                "Signal",
                "Entry",
                "StopLoss",
                "Target",
                "Status"
            ]
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(trade_data)

def monitor_trade(current_price, trade):
    """
    Monitor paper trade status.
    """

    if current_price >= trade["Target"]:
        return "TARGET HIT"

    elif current_price <= trade["StopLoss"]:
        return "STOP LOSS HIT"

    return "OPEN"