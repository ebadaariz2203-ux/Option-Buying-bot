import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt


def plot_equity_curve():

    file_name = "trade_history/trade_history.csv"

    if not os.path.exists(file_name):
        print("Trade history not found.")
        return

    equity = 0
    equity_curve = [0]

    with open(file_name, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:

            pnl_value = row.get("PnL", "").strip()

            if pnl_value == "":
                continue

            equity += float(pnl_value)
            equity_curve.append(equity)

    plt.figure(figsize=(10, 5))

    plt.plot(
        equity_curve,
        linewidth=2,
    )

    plt.title("Equity Curve")
    plt.xlabel("Trades")
    plt.ylabel("Profit")
    plt.grid(True)
    plt.show()


def plot_drawdown():

    file_name = "trade_history/trade_history.csv"

    if not os.path.exists(file_name):
        return

    equity = 0
    peak = 0
    drawdown = []

    with open(file_name, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:

            equity += float(row["PnL"]) if row["PnL"] else 0

            if equity > peak:
                peak = equity

            drawdown.append(peak - equity)

    plt.figure(figsize=(10, 5))

    plt.plot(drawdown)

    plt.title("Drawdown")
    plt.xlabel("Trades")
    plt.ylabel("Drawdown")
    plt.grid(True)
    plt.show()


def plot_win_loss():

    file_name = "trade_history/trade_history.csv"

    if not os.path.exists(file_name):
        return

    win = 0
    loss = 0

    with open(file_name, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:

            pnl = float(row["PnL"])

            if pnl > 0:
                win += 1

            elif pnl < 0:
                loss += 1

    plt.figure(figsize=(5, 5))

    plt.pie(
        [win, loss],
        labels=["Win", "Loss"],
        autopct="%1.1f%%",
    )

    plt.title("Win / Loss Distribution")
    plt.show()


def monthly_summary():

    file_name = "trade_history/trade_history.csv"

    if not os.path.exists(file_name):
        return

    monthly = defaultdict(float)

    with open(file_name, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:

            month = row["Date"][:7]
            monthly[month] += float(row["PnL"])

    print("\nMonthly Summary\n")

    for month, pnl in monthly.items():

        print(month, ":", round(pnl, 2))


def show_dashboard():

    plot_equity_curve()
    plot_drawdown()
    plot_win_loss()

    # monthly_summary()   # Day 77 ke baad enable karenge