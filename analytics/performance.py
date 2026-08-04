import csv
import os

import statistics
def calculate_max_drawdown(equity_curve):

    peak = equity_curve[0]
    max_drawdown = 0

    for value in equity_curve:

        if value > peak:
            peak = value

        drawdown = peak - value

        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return round(max_drawdown, 2)


def calculate_profit_factor(trades):

    gross_profit = sum(t for t in trades if t > 0)
    gross_loss = abs(sum(t for t in trades if t < 0))

    if gross_loss == 0:
        return 0

    return round(gross_profit / gross_loss, 2)


def calculate_expectancy(trades):

    if len(trades) == 0:
        return 0

    return round(sum(trades) / len(trades), 2)


def calculate_sharpe_ratio(trades):

    if len(trades) < 2:
        return 0

    avg = statistics.mean(trades)
    std = statistics.stdev(trades)

    if std == 0:
        return 0

    return round(avg / std, 2)


def calculate_performance():

    file_name = "trade_history/trade_history.csv"

    if not os.path.exists(file_name):
        return None

    total_trades = 0
    winning_trades = 0
    losing_trades = 0

    total_pnl = 0
    total_profit = 0
    total_loss = 0

    best_trade = float("-inf")
    worst_trade = float("inf")
    trades = []
    equity_curve = []
    equity = 0

    with open(file_name, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:

            if row["PnL"] == "":
                continue

            pnl = float(row["PnL"])

            trades.append(pnl)

            equity += pnl
            equity_curve.append(equity)

            total_pnl += pnl

            if pnl > 0:
                winning_trades += 1
                total_profit += pnl

            elif pnl < 0:
                losing_trades += 1
                total_loss += pnl

            if pnl > best_trade:
                best_trade = pnl

            if pnl < worst_trade:
                worst_trade = pnl

    win_rate = 0

    if total_trades > 0:
        win_rate = round(
            (winning_trades / total_trades) * 100,
            2,
        )

    average_profit = 0

    if winning_trades > 0:
        average_profit = round(
            total_profit / winning_trades,
            2,
        )

    average_loss = 0

    if losing_trades > 0:
        average_loss = round(
            total_loss / losing_trades,
            2,
        )

    return {
        "TotalTrades": total_trades,
        "WinningTrades": winning_trades,
        "LosingTrades": losing_trades,
        "TotalPnL": round(total_pnl, 2),
        "WinRate": win_rate,
        "AverageProfit": average_profit,
        "AverageLoss": average_loss,
        "BestTrade": round(best_trade, 2) if total_trades > 0 else 0,
        "WorstTrade": round(worst_trade, 2) if total_trades > 0 else 0,
        
        "MaxDrawdown": calculate_max_drawdown(equity_curve) if equity_curve else 0,
        "ProfitFactor": calculate_profit_factor(trades),
        "Expectancy": calculate_expectancy(trades),
        "SharpeRatio": calculate_sharpe_ratio(trades),
    }
    