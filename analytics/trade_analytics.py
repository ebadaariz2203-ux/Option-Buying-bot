def calculate_trade_analytics(trades):
    """
    Calculate detailed trade statistics.
    trades: list of completed trades
    Each trade should contain a 'PnL' field.
    """

    # FIX: used to return {} for an empty trade list, which crashed
    # run_backtest.py with a KeyError the moment it read
    # trade_stats['Average Winner'] on any zero-trade day/dataset.
    # Returning the same keys with zeroed-out values keeps the
    # contract consistent for every caller instead of requiring each
    # one to special-case "no trades".
    if not trades:
        return {
            "Average Winner": 0,
            "Average Loser": 0,
            "Largest Winner": 0,
            "Largest Loser": 0,
            "Max Win Streak": 0,
            "Max Loss Streak": 0,
        }

    pnl_list = [trade["PnL"] for trade in trades]

    winners = [p for p in pnl_list if p > 0]
    losers = [p for p in pnl_list if p < 0]

    avg_win = round(sum(winners) / len(winners), 2) if winners else 0
    avg_loss = round(sum(losers) / len(losers), 2) if losers else 0

    largest_win = round(max(winners), 2) if winners else 0
    largest_loss = round(min(losers), 2) if losers else 0

    max_win_streak = 0
    max_loss_streak = 0

    current_win = 0
    current_loss = 0

    for pnl in pnl_list:

        if pnl > 0:
            current_win += 1
            current_loss = 0

        elif pnl < 0:
            current_loss += 1
            current_win = 0

        else:
            current_win = 0
            current_loss = 0

        max_win_streak = max(max_win_streak, current_win)
        max_loss_streak = max(max_loss_streak, current_loss)

    return {
        "Average Winner": avg_win,
        "Average Loser": avg_loss,
        "Largest Winner": largest_win,
        "Largest Loser": largest_loss,
        "Max Win Streak": max_win_streak,
        "Max Loss Streak": max_loss_streak,
    }