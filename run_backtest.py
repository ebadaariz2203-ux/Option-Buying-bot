from logger.logger import logger

from market_data.market_data import get_nifty_data

from backtest.backtest import run_backtest

from backtest.report import save_backtest_report


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

    report = save_backtest_report(backtest["TradeLog"])

    print(f"\nReport Saved : {report}")


if __name__ == "__main__":
    main()