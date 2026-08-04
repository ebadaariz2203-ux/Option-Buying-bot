import statistics

from backtest.simulator import simulate_trade
from risk.risk_manager import calculate_trade
from strategy.strategy import generate_signal
from option_chain.option_data import get_option_chain


def run_backtest(data):

    signals = []
    trade_log = []
    trade_returns = []

    total_pnl = 0
    gross_profit = 0
    gross_loss = 0
    average_win = 0
    average_loss = 0
    expectancy = 0

    equity = 0

    peak_equity = 0

    max_drawdown = 0
    trade_returns = []

    sharpe_ratio = 0

    winning_trades = 0
    losing_trades = 0
    eod_exit_trades = 0

    for i in range(20, len(data)):

        candle = data.iloc[: i + 1]

        close_price = float(candle.iloc[-1]["Close"])

        
        
        signal = generate_signal(
            candle,
            option=None,
            debug=False,
        )
        if signal != "NO TRADE":

            entry = close_price

            atr = float(candle.iloc[-1]["ATR"])

            trade = calculate_trade(entry, atr)

            future_data = data.iloc[i + 1:i + 11]

            result = simulate_trade(
                signal,
                trade["Entry"],
                trade["StopLoss"],
                trade["Target"],
                future_data,
            )
            trade_log.append({
                "Signal": signal,
                "Entry": trade["Entry"],
                "StopLoss": trade["StopLoss"],
                "Target": trade["Target"],
                "Exit": result["Exit"],
                "Result": result["Result"],
                "HoldingCandles": result["HoldingCandles"],
                "PnL": round(result["Exit"] - trade["Entry"], 2),
            })
            
            if signal != "NO TRADE":

                
                if result["Result"] == "WIN":

                    winning_trades += 1

                    pnl = trade["Target"] - trade["Entry"]

                    total_pnl += pnl
                    gross_profit += pnl
                    trade_returns.append(pnl)

                elif result["Result"] == "LOSS":

                    losing_trades += 1

                    pnl = trade["StopLoss"] - trade["Entry"]

                    total_pnl += pnl
                    gross_loss += abs(pnl)
                    trade_returns.append(pnl)

                elif result["Result"] == "EOD EXIT":

                    eod_exit_trades += 1

                    pnl = result["Exit"] - trade["Entry"]

                    total_pnl += pnl
                
                    if pnl > 0:
                        gross_profit += pnl
                        
                    elif pnl < 0:
                        gross_loss += abs(pnl)

                    trade_returns.append(pnl)                        

                equity += pnl
                
                if equity > peak_equity:
                    peak_equity = equity

                drawdown = peak_equity - equity

                if drawdown > max_drawdown:
                    max_drawdown = drawdown

                signals.append(result["Result"])
            else:

                signals.append("NO TRADE")
                    
    
    no_trade = signals.count("NO TRADE")
    win_rate = 0

    if (winning_trades + losing_trades) > 0:

        win_rate = round(
        (winning_trades /
        (winning_trades + losing_trades)) * 100,
        2,
        )
    profit_factor = 0

    if gross_loss > 0:

        profit_factor = round(
            gross_profit / gross_loss,
            2,
        )
    if winning_trades > 0:

        average_win = gross_profit / winning_trades

    if losing_trades > 0:

        average_loss = gross_loss / losing_trades

    win_rate_decimal = 0
    loss_rate_decimal = 0

    if (winning_trades + losing_trades) > 0:

        win_rate_decimal = winning_trades / (winning_trades + losing_trades)

        loss_rate_decimal = losing_trades / (winning_trades + losing_trades)

    expectancy = round(
        (win_rate_decimal * average_win)
        - (loss_rate_decimal * average_loss),
        2,
    )

    if len(trade_returns) > 1:

        avg_return = statistics.mean(trade_returns)

        std_return = statistics.stdev(trade_returns)

        if std_return > 0:

            sharpe_ratio = round(
                avg_return / std_return,
                2,
            )
    return {
        "Results": signals,
        "TradeLog": trade_log,
        "Wins": winning_trades,
        "Losses": losing_trades,
        "EODExits": eod_exit_trades,
        "NoTrade": no_trade,
        "TotalTrades": len(trade_log),
        "TotalCandles": len(data),
        "WinRate": win_rate,
        "NetPnL": round(total_pnl, 2),
        "ProfitFactor": profit_factor,
        "MaximumDrawdown": round(max_drawdown, 2),
        "Expectancy": expectancy,
        "SharpeRatio": sharpe_ratio,
    }