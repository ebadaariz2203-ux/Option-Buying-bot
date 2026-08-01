import csv
import os


def calculate_equity_curve():

    file_name = "trade_history/trade_history.csv"

    if not os.path.exists(file_name):
        return []

    equity = 100000
    curve = []

    with open(file_name, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:

            pnl = float(row["PnL"])

            equity += pnl

            curve.append(round(equity, 2))

    return curve