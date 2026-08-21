import csv
import os
from datetime import datetime


def save_backtest_report(trade_log, trade_stats=None):

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
        if trade_stats:

            writer.writerow([])
            writer.writerow(["TRADE ANALYTICS"])

            writer.writerow(["Average Winner", trade_stats["Average Winner"]])
            writer.writerow(["Average Loser", trade_stats["Average Loser"]])
            writer.writerow(["Largest Winner", trade_stats["Largest Winner"]])
            writer.writerow(["Largest Loser", trade_stats["Largest Loser"]])
            writer.writerow(["Max Win Streak", trade_stats["Max Win Streak"]])
            writer.writerow(["Max Loss Streak", trade_stats["Max Loss Streak"]])

        return filename