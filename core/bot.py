import time

from logger.logger import logger
from market_data.market_data import get_nifty_data

from indicators.indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_volume_average,
    calculate_atr,
)

from option_chain.option_data import get_option_chain
from strategy.strategy import generate_signal
from strategy.strike_selector import select_best_strike

from risk.position_size import calculate_position_size
from risk.risk_manager import calculate_trade, calculate_pnl

from paper_trade.trade_validator import validate_trade
from paper_trade.paper_trade import (
    execute_paper_trade,
    save_trade,
    monitor_trade,
)

from telegram.telegram_bot import send_telegram_message
from utils.market_session import is_market_open
from market_simulator.simulator import simulate_price

from trade.pnl_engine import get_trade_status
from trade.trade_state import TradeState
from trade.order_manager import OrderManager
from trade.order_history import save_order_history
from trade.position_manager import PositionManager

from broker.paper_broker import PaperBroker

from trade_history.trade_history import save_trade_history

from analytics.performance import calculate_performance
from analytics.equity_curve import calculate_equity_curve

from backtest.backtest import run_backtest
from backtest.report import save_backtest_report

from reports.dashboard import show_dashboard
from portfolio.portfolio_manager import portfolio_summary
from trade.position_monitor import PositionMonitor

class TradingBot:

    def __init__(self):

        print("=" * 50)
        print("Trading Bot Initialized")
        print("=" * 50)

        self.trade_state = TradeState()
        self.broker = PaperBroker()
        self.order_manager = OrderManager(self.broker)
        self.position_manager = PositionManager(self.trade_state)
        self.position_monitor = PositionMonitor(self.position_manager)

    def run_continuously(self):

        print("\n========== LIVE TRADING STARTED ==========\n")

        try:

            while True:

                if self.check_market_session():

                    print("\nRunning Trading Cycle...\n")

                    self.run()

                else:

                    print("\nMarket Closed.")

                print("\nNext Scan in 5 Minutes...\n")

                time.sleep(300)

        except KeyboardInterrupt:

            print("\nStopping Trading Bot...")

        finally:

            print("Trading Bot Closed Successfully.")
    def fetch_market_data(self):
        logger.info("Downloading Market Data...")
        data = get_nifty_data()
        return data

    def calculate_indicators(self, data):

        data = calculate_ema(data)
        data = calculate_rsi(data)
        data = calculate_volume_average(data)
        data = calculate_atr(data)

        return data

    def generate_trading_signal(self, data):

        close_price = float(data.iloc[-1]["Close"])

        option = get_option_chain(close_price)
        print("\n========== AVAILABLE STRIKES ==========")

        for strike in option["Strikes"]:
            print(
                f"{strike['Strike']} {strike['Type']} | "
                f"OI: {strike['OI']} | "
                f"Volume: {strike['Volume']}"
            )

        print("=======================================")
        print("\n========== OPTION CHAIN ==========")
        print(f"PCR        : {option['PCR']}")
        print(f"Call OI    : {option['Call_OI']}")
        print(f"Put OI     : {option['Put_OI']}")
        print(f"ATM Strike : {option['ATM_Strike']}")
        print("==================================")

        signal = generate_signal(
            data,
            option,
            debug=True,
        )
        selected_strike = select_best_strike(signal, option)

        print(f"\nTrading Signal : {signal}")

        if selected_strike:
           print(
                f"Selected Strike: "
                f"{selected_strike['Strike']} {selected_strike['Type']}"
            )
        else:
            print("Selected Strike: None (No Trade Signal)")

        logger.info(f"Trading Signal : {signal}")

        return signal, selected_strike

    def manage_risk(self, signal, data):

        entry_price = 180.00
        atr = float(data.iloc[-1]["ATR"])

        trade = calculate_trade(entry_price, atr)
        position = calculate_position_size(
                    trade["Entry"],
                    trade["StopLoss"]
        )
        trade["Quantity"] = position["Quantity"]
        validation = validate_trade(position)
     
        return trade, position, validation

    def execute_trade_flow(self, signal, trade, selected_strike):

    # Place Order
        paper_trade = self.order_manager.place_order(signal, trade)

        # Save Order History
        save_order_history(paper_trade)

        # Add Trade Details
        paper_trade["Strike"] = selected_strike["Strike"]
        paper_trade["OptionType"] = selected_strike["Type"]
        paper_trade["Quantity"] = trade["Quantity"]

        # Open Position
        self.position_manager.open_position(paper_trade)

        # Show Active Position
        self.position_manager.print_position()

        # Save Trade
        save_trade(paper_trade)

        # Telegram Notification
        message = f"""
    📢 OPTION BUYING BOT

    Signal : {signal}

    Entry : {paper_trade['Entry']}
    Stop Loss : {paper_trade['StopLoss']}
    Target : {paper_trade['Target']}

    Status : {paper_trade['Status']}
    """

        self.send_notification(message)

        # Print Trade
        self.print_paper_trade(paper_trade)

        return paper_trade
    def monitor_open_trade(self, trade):
        """
        Monitor paper trade using simulated prices.
        """

        if not self.position_manager.has_position():

            print("\nNo Active Position")

            return None

        current_price = trade["Entry"]
        start_time = time.time()

        print("\n========== TRADE MONITOR ==========")

        for i in range(5):

            # Simulate live price
            current_price = simulate_price(current_price)

            # Check trade status (OPEN / TARGET / STOP LOSS)
            trade_status = monitor_trade(current_price, trade)

            if trade_status == "TARGET HIT":
                print("\nTarget Achieved!")
                break

            if trade_status == "STOP LOSS HIT":
                print("\nStop Loss Triggered!")
                break

            # Calculate Real-Time P&L
            pnl_info = get_trade_status(
                entry_price=trade["Entry"],
                current_price=current_price,
                quantity=1,
            )

            print(f"""
        Update #{i+1}

        Current Price : {pnl_info['CurrentPrice']}
        PnL           : {pnl_info['PnL']}
        Return        : {pnl_info['Return']} %
        Trade Status  : {trade_status}
        """)

            if trade_status != "OPEN":
                break

            time.sleep(2)

        # ===============================
        # Loop finished
        # ===============================

        exit_price = current_price
        end_time = time.time()

        duration_seconds = int(end_time - start_time)

        minutes = duration_seconds // 60
        seconds = duration_seconds % 60

        duration = f"{minutes}m {seconds}s"

        result = calculate_pnl(
            trade["Entry"],
            exit_price,
        )
        result["Time"] = trade["Time"]
        result["Signal"] = trade["Signal"]
        result["Duration"] = duration
        result["StopLoss"] = trade["StopLoss"]
        result["Target"] = trade["Target"]
        result["Status"] = trade_status
        save_trade_history(result)
        self.position_manager.close_position()

        print("\nPosition Closed Successfully.")

        print("\n========== FINAL RESULT ==========")
        print(f"Entry  : {result['Entry']}")
        print(f"Exit   : {result['Exit']}")
        print(f"PnL    : {result['PnL']}")
        print(f"Return : {result['PnLPercent']} %")
        print("===================================")

        return result

    def send_notification(self, message):

        send_telegram_message(message)

    def check_market_session(self):

        if is_market_open():
            return True

        print("Market is Closed.")
        return False

    def print_trade_details(self, trade):

        print("\n========== TRADE DETAILS ==========")
        print(f"Entry Price : {trade['Entry']}")
        print(f"ATR         : {trade['ATR']}")
        print(f"ATR Mult.   : {trade['ATRMultiplier']}")
        print(f"RiskReward  : 1:{trade['RiskReward']}")
        print(f"Stop Loss   : {trade['StopLoss']}")
        print(f"Target      : {trade['Target']}")
        print("===================================")

    def print_position_size(self, position):

        print("\n========== POSITION SIZE ==========")
        print(f"Capital      : {position['Capital']}")
        print(f"Risk %       : {position['RiskPercent']}%")
        print(f"Max Loss     : {position['MaxLoss']}")
        print(f"Risk / Lot   : {position['RiskPerLot']}")
        print(f"Lots to Buy  : {position['Lots']}")
        print(f"Quantity     : {position['Quantity']}")
        print(f"Enough Cap.  : {position['EnoughCapital']}")
        print(f"Required Cap.: {position['RequiredCapital']}")
        print("===================================")

    def print_validation(self, validation):

        print("\n========== TRADE VALIDATION ==========")
        print(f"Allowed : {validation['Allowed']}")
        print(f"Reason  : {validation['Reason']}")
        print("======================================")
    def print_portfolio(self, portfolio):

        print("\n========== PORTFOLIO ==========")

        print(f"Initial Capital : {portfolio['InitialCapital']}")
        print(f"Current Balance : {portfolio['CurrentBalance']}")
        print(f"Net Profit      : {portfolio['Profit']}")
        print(f"Return %        : {portfolio['ReturnPercent']}")

        print("================================")

    def print_paper_trade(self, paper_trade):

        print("\n========== PAPER TRADE ==========")
        print(f"Time        : {paper_trade['Time']}")
        print(f"Signal      : {paper_trade['Signal']}")
        print(f"Entry       : {paper_trade['Entry']}")
        print(f"Stop Loss   : {paper_trade['StopLoss']}")
        print(f"Target      : {paper_trade['Target']}")
        print(f"Status      : {paper_trade['Status']}")
        print("=================================")

    
    def handle_validation(self, validation):

        if validation["Allowed"]:
            return True

        print("\nTrade Rejected.")
        print(validation["Reason"])

        return False

    def show_performance(self):

        performance = calculate_performance()

        if not performance:
            return

        print("\n========== PERFORMANCE ==========")

        print(f"Total Trades   : {performance['TotalTrades']}")
        print(f"Winning Trades : {performance['WinningTrades']}")
        print(f"Losing Trades  : {performance['LosingTrades']}")
        print(f"Win Rate       : {performance['WinRate']} %")
        print(f"Total P&L      : {performance['TotalPnL']}")
        print(f"Avg Profit     : {performance['AverageProfit']}")
        print(f"Avg Loss       : {performance['AverageLoss']}")
        print(f"Best Trade     : {performance['BestTrade']}")
        print(f"Worst Trade    : {performance['WorstTrade']}")

        print(f"Max Drawdown   : {performance['MaxDrawdown']}")
        print(f"Profit Factor  : {performance['ProfitFactor']}")
        print(f"Expectancy     : {performance['Expectancy']}")
        print(f"Sharpe Ratio   : {performance['SharpeRatio']}")

        print("==================================")

    def show_equity_curve(self):

        equity = calculate_equity_curve()

        if not equity:
            return

        print("\n========== EQUITY CURVE ==========")

        for i, value in enumerate(equity, start=1):

            print(f"Trade {i} : {value}")

        
        print("=================================")

    def print_backtest_report(self, backtest):

        print("\n========== BACKTEST REPORT ==========")
        print(f"Total Candles : {backtest['TotalCandles']}")
        print(f"Total Trades  : {backtest['TotalTrades']}")
        print(f"Wins          : {backtest['Wins']}")
        print(f"Losses        : {backtest['Losses']}")
        print(f"EOD Exits     : {backtest['EODExits']}")
        print(f"No Trade      : {backtest['NoTrade']}")
        print(f"Win Rate      : {backtest['WinRate']} %")
        print(f"Profit Factor : {backtest['ProfitFactor']}")
        print(f"Max Drawdown : {backtest['MaximumDrawdown']}")
        print(f"Net P&L       : {backtest['NetPnL']}")
        print(f"Expectancy   : {backtest['Expectancy']}")
        print(f"Sharpe Ratio : {backtest['SharpeRatio']}")
        print("=====================================")

        print("\n========== TRADE LOG ==========")

        for i, trade in enumerate(backtest["TradeLog"], start=1):

            print(
                f"{i}. "
                f"{trade['Signal']} | "
                f"Entry: {trade['Entry']:.2f} | "
                f"Exit: {trade['Exit']:.2f} | "
                f"{trade['Result']} | "
                f"PnL: {trade['PnL']:.2f}"
            )

        print("================================")

    def run_backtest_flow(self, data):

        backtest = run_backtest(data)

        self.print_backtest_report(backtest)

        report_file = save_backtest_report(backtest["TradeLog"])

        print(f"\nBacktest Report Saved : {report_file}")

        return backtest

    def run(self):

        data = self.fetch_market_data()

        data = self.calculate_indicators(data)

        self.run_backtest_flow(data)

        signal, selected_strike = self.generate_trading_signal(data)

        if signal == "NO TRADE":
            print("\nNo Trade Found.")
            return

        # Duplicate Trade Protection
        if self.trade_state.is_trade_open():

            current_trade = self.trade_state.get_trade()

            print("\n========== ACTIVE TRADE ==========")
            print(f"Entry     : {current_trade['Entry']}")
            print(f"Target    : {current_trade['Target']}")
            print(f"Stop Loss : {current_trade['StopLoss']}")
            print("==================================")
            print("Trade Already Open")
            print("Skipping New Signal...")

            return
      
        trade, position, validation = self.manage_risk(signal, data)

        self.print_trade_details(trade)
        self.print_position_size(position)
        self.print_validation(validation)
        portfolio = portfolio_summary()

        self.print_portfolio(portfolio)

        if not self.handle_validation(validation):
            return

        paper_trade = self.execute_trade_flow(
            signal,
            trade,
            selected_strike,
        )

        self.monitor_open_trade(paper_trade)
       
        self.show_performance()

        self.show_equity_curve()

        show_dashboard()
            
           