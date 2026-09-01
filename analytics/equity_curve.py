import csv
import os


def calculate_equity_curve():

    # FIX: was reading trade_history/trade_history.csv, a file nothing
    # in the current pipeline writes to (save_trade_history() writes
    # completed_trade_history.csv, which analytics/performance.py
    # already reads correctly). This meant the equity curve silently
    # showed stale/empty data instead of matching the real performance
    # numbers shown right next to it.
    file_path = "trade_history/completed_trade_history.csv"

    equity = 0
    equity_curve = []

    if not os.path.exists(file_path):
        return equity_curve


    with open(file_path, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:

            pnl_value = (row.get("PnL") or "").strip()

            if pnl_value == "":
                continue

            try:
                pnl = float(pnl_value)

            except ValueError:
                continue

            equity += pnl

            equity_curve.append(equity)
    return equity_curve