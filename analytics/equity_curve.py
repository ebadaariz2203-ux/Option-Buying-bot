import csv
import os


def calculate_equity_curve():

    file_path = "trade_history/trade_history.csv"

    equity = 0
    equity_curve = []

    if not os.path.exists(file_path):
        return equity_curve


    with open(file_path, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:

            pnl_value = row.get("PnL", "").strip()

            if pnl_value == "":
                continue

            try:
                pnl = float(pnl_value)

            except ValueError:
                continue

            equity += pnl

            equity_curve.append(equity)
    return equity_curve