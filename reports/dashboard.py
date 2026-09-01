import csv
import os
from collections import defaultdict

import matplotlib

# FIX: this dashboard runs inside the unattended trading-bot loop
# (core/bot.py calls show_dashboard() at the end of every run() cycle,
# right after a trade closes). The previous plt.show() calls opened a
# blocking GUI window ("Figure 1") and froze the ENTIRE bot process
# until someone manually closed it — on 2026-08-31 nobody was there
# to close it after the 11:27 AM TIME EXIT, so the bot sat frozen for
# the rest of the day and never scanned again. Force the non-interactive
# "Agg" backend and save charts to PNG files instead of displaying them.
matplotlib.use("Agg")

import matplotlib.pyplot as plt

CHARTS_DIR = "reports/charts"


def plot_equity_curve():

    file_name = "trade_history/completed_trade_history.csv"

    if not os.path.exists(file_name):
        print("Trade history not found.")
        return

    equity = 0
    equity_curve = [0]

    with open(file_name, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:

            pnl_value = (row.get("PnL") or "").strip()

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
    _save_and_close("equity_curve.png")


def plot_drawdown():

    # FIX: was reading trade_history/trade_history.csv, a file nothing
    # in the current pipeline writes to. Now matches plot_equity_curve()
    # / monthly_summary() below, which already correctly read
    # completed_trade_history.csv (see analytics/equity_curve.py for
    # the same fix).
    file_name = "trade_history/completed_trade_history.csv"

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
    _save_and_close("drawdown.png")


def plot_win_loss():

    # FIX: same stale-file issue as plot_drawdown() above.
    file_name = "trade_history/completed_trade_history.csv"

    if not os.path.exists(file_name):
        return

    win = 0
    loss = 0

    with open(file_name, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:

            if not row["PnL"]:
                continue

            pnl = float(row["PnL"])

            if pnl > 0:
                win += 1

            elif pnl < 0:
                loss += 1
    if win == 0 and loss == 0:
        print("No valid Win/Loss data available.")
        return
    plt.figure(figsize=(5, 5))

    plt.pie(
        [win, loss],
        labels=["Win", "Loss"],
        autopct="%1.1f%%",
    )

    plt.title("Win / Loss Distribution")
    _save_and_close("win_loss.png")


def monthly_summary():

    file_name = "trade_history/completed_trade_history.csv"

    if not os.path.exists(file_name):
        return

    monthly = defaultdict(float)

    with open(file_name, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:

            month = row["Date"][:7]
            if not row["PnL"]:
                continue

            monthly[month] += float(row["PnL"])

    print("\nMonthly Summary\n")

    for month, pnl in monthly.items():

        print(month, ":", round(pnl, 2))


def _save_and_close(filename):
    """Write the current figure to CHARTS_DIR and free it — never blocks."""

    os.makedirs(CHARTS_DIR, exist_ok=True)
    out_path = os.path.join(CHARTS_DIR, filename)
    plt.savefig(out_path)
    plt.close()
    print(f"Chart saved: {out_path}")


def show_dashboard():

    plot_equity_curve()
    plot_drawdown()
    plot_win_loss()

    # monthly_summary()   # Day 77 ke baad enable karenge
