import csv
import os
from datetime import datetime


def load_trade_history():

    file_name = "trade_history/trade_history.csv"

    if not os.path.exists(file_name):
        return []

    with open(file_name, "r") as file:

        reader = csv.DictReader(file)

        return list(reader)


def save_trade_history(result):

    file_name = "trade_history/completed_trade_history.csv"
    os.makedirs("trade_history", exist_ok=True)

    file_exists = os.path.exists(file_name)

    now = datetime.now()

    trade_date = now.strftime("%Y-%m-%d")
    exit_time = now.strftime("%H:%M:%S")

    with open(file_name, "a", newline="") as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "Date",
                "EntryTime",
                "ExitTime",
                "Signal",
                "Entry",
                "Exit",
                "StopLoss",
                "Target",
                "Status",
                "PnL",
                "Return",
            ])

        writer.writerow([
            trade_date,
            result["Time"],
            exit_time,
            result["Signal"],
            result["Entry"],
            result["Exit"],
            result["StopLoss"],
            result["Target"],
            result["Status"],
            result["PnL"],
            result["PnLPercent"],
        ])
