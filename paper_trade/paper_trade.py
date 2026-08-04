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

        "OrderID": trade.get("OrderID", ""),
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "Signal": signal,

        "Status": "OPEN",

        "Entry": trade["Entry"],

        "Target": trade["Target"],

        "StopLoss": trade["StopLoss"],


        "ATR": trade.get("ATR", 0),

        "ATRMultiplier": trade.get("ATRMultiplier", 0),

        "RiskReward": trade.get("RiskReward", 0),


        "Strike": trade.get("Strike", 0),

        "OptionType": trade.get("OptionType", ""),


        "Quantity": trade.get("Quantity", 0),


        "PnL": ""

    }


    return trade_data


def save_trade(trade_data):

    file_name = "trade_history/trade_history.csv"
    file_exists = os.path.isfile(file_name)

    with open(file_name, mode="a", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "OrderID",
                "Timestamp",
                "Time",
                "Signal",
                "Status",
                "Entry",
                "Target",
                "StopLoss",
                "ATR",
                "ATRMultiplier",
                "RiskReward",
                "Strike",
                "OptionType",
                "Quantity",
                "PnL"
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