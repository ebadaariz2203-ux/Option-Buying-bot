from logger.logger import logger

from market_data.market_data import get_nifty_data

from backtest.backtest import run_backtest

from backtest.report import save_backtest_report

from analytics.trade_analytics import calculate_trade_analytics


def main():

    logger.info("Running Backtest...")

    data = get_nifty_data()

    backtest = run_backtest(data)

    print("\n========== BACKTEST REPORT ==========")
    print(f"Total Candles : {backtest['TotalCandles']}")
    print(f"Total Trades  : {backtest['TotalTrades']}")
    print(f"Wins          : {backtest['Wins']}")
    print(f"Losses        : {backtest['Losses']}")
    print(f"EOD Exits     : {backtest['EODExits']}")
    print(f"No Trade      : {backtest['NoTrade']}")
    print(f"Win Rate      : {backtest['WinRate']} %")
    print(f"Net P&L       : {backtest['NetPnL']}")
    print("=====================================")

    trade_stats = calculate_trade_analytics(backtest["TradeLog"])

    print("\n========== TRADE ANALYTICS ==========")
    print(f"Average Winner   : {trade_stats['Average Winner']}")
    print(f"Average Loser    : {trade_stats['Average Loser']}")
    print(f"Largest Winner   : {trade_stats['Largest Winner']}")
    print(f"Largest Loser    : {trade_stats['Largest Loser']}")
    print(f"Max Win Streak   : {trade_stats['Max Win Streak']}")
    print(f"Max Loss Streak  : {trade_stats['Max Loss Streak']}")
    print("=====================================")

   
    report = save_backtest_report(backtest["TradeLog"])

    print(f"\nReport Saved : {report}")

if __name__ == "__main__":
    main()