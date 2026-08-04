import csv
import os
from datetime import datetime


def save_backtest_report(trade_log):

    folder = "backtest/reports"

    os.makedirs(folder, exist_ok=True)

    filename = (
        f"{folder}/backtest_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    with open(filename, "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "Signal",
            "Entry",
            "StopLoss",
            "Target",
            "Exit",
            "Result",
            "HoldingCandles",
            "PnL",
        ])

        for trade in trade_log:

            writer.writerow([
                trade["Signal"],
                trade["Entry"],
                trade["StopLoss"],
                trade["Target"],
                trade["Exit"],
                trade["Result"],
                trade["HoldingCandles"],
                trade["PnL"],
            ])

    return filename