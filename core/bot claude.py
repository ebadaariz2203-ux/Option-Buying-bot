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
from risk.risk_manager import calculate_trade
from risk.position_size import calculate_position_size
from paper_trade.trade_validator import validate_trade
from paper_trade.paper_trade import (

        execute_paper_trade,
        save_trade,
        check_trade_status,
        monitor_trade,
)
from telegram.telegram_bot import send_telegram_message

from utils.market_session import is_market_open

from market_simulator.simulator import simulate_price

from trade.pnl_engine import get_trade_status, calculate_pnl


class TradingBot:

    def __init__(self):
        print("Trading Bot Initialized")

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

        signal = generate_signal(data, option)
        selected_strike = select_best_strike(signal, option)

        print(f"\nTrading Signal : {signal}")
        if selected_strike:
            print(f"Selected Strike: {selected_strike}")
        else:
            print("Selected Strike: None (No Trade Signal)")

        logger.info(f"Trading Signal : {signal}")

        return signal

    def manage_risk(self, signal, data):

        entry_price = 180.00
        atr = float(data.iloc[-1]["ATR"])

        trade = calculate_trade(entry_price, atr)

        position = calculate_position_size(
            trade["Entry"],
            trade["StopLoss"]
        )

        validation = validate_trade(position)

        return trade, position, validation

    def execute_trade(self, signal, trade):

        paper_trade = execute_paper_trade(signal, trade)

        save_trade(paper_trade)

        return paper_trade

    def get_trade_status(self, current_price, trade):

        status = check_trade_status(current_price, trade)

        return status

    def monitor_open_trade(self, trade):
        """
        Monitor paper trade using simulated prices.
        """

        current_price = trade["Entry"]

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
            pnl_status = get_trade_status(
                entry_price=trade["Entry"],
                current_price=current_price,
                quantity=1,   # Temporary
            )

            print(f"""
        Update #{i+1}

        Current Price : {pnl_status['CurrentPrice']}
        PnL           : {pnl_status['PnL']}
        Return        : {pnl_status['Return']} %
        Trade Status  : {trade_status}
        """)

            if trade_status != "OPEN":
                break

            time.sleep(2)

        # ===============================
        # Loop finished
        # ===============================

        exit_price = current_price

        result = calculate_pnl(
            trade["Entry"],
            exit_price,
        )

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
        print("===================================")

    def print_validation(self, validation):

        print("\n========== TRADE VALIDATION ==========")
        print(f"Allowed : {validation['Allowed']}")
        print(f"Reason  : {validation['Reason']}")
        print("======================================")

    def print_paper_trade(self, paper_trade):

        print("\n========== PAPER TRADE ==========")
        print(f"Time        : {paper_trade['Time']}")
        print(f"Signal      : {paper_trade['Signal']}")
        print(f"Entry       : {paper_trade['Entry']}")
        print(f"Stop Loss   : {paper_trade['StopLoss']}")
        print(f"Target      : {paper_trade['Target']}")
        print(f"Status      : {paper_trade['Status']}")
        print("=================================")

    def execute_trade_flow(self, signal, trade):

        paper_trade = self.execute_trade(signal, trade)

        message = f"""
    📢 OPTION BUYING BOT

    Signal : {signal}

    Entry : {trade['Entry']}
    Stop Loss : {trade['StopLoss']}
    Target : {trade['Target']}

    Status : OPEN
        """

        self.send_notification(message)

        self.print_paper_trade(paper_trade)

        self.monitor_open_trade(trade)

        return paper_trade

    def handle_validation(self, validation):

        if validation["Allowed"]:
            return True

        print("\nTrade Rejected.")
        print(validation["Reason"])

        return False

    def run(self):

        if not self.check_market_session():
            return

        data = self.fetch_market_data()

        data = self.calculate_indicators(data)

        signal = self.generate_trading_signal(data)

        if signal == "NO TRADE":
            print("\nNo Trade Found.")
            return

        trade, position, validation = self.manage_risk(signal, data)

        self.print_trade_details(trade)
        self.print_position_size(position)
        self.print_validation(validation)

        if not self.handle_validation(validation):
            return

        self.execute_trade_flow(signal, trade)
