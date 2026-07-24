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
from risk.risk_manager import calculate_trade
from risk.position_size import calculate_position_size
from paper_trade.trade_validator import validate_trade
from paper_trade.paper_trade import (

        execute_paper_trade,
        save_trade,
        check_trade_status,
)
from telegram.telegram_bot import send_telegram_message
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

        option = get_option_chain()

        print("\n========== OPTION CHAIN ==========")
        print(f"PCR        : {option['PCR']}")
        print(f"Call OI    : {option['Call_OI']}")
        print(f"Put OI     : {option['Put_OI']}")
        print(f"ATM Strike : {option['ATM_Strike']}")
        print("==================================")

        signal = generate_signal(data, option)

        print(f"\nTrading Signal : {signal}")
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
    
    def send_notification(self, message):

        send_telegram_message(message)

    def run(self):
        data = self.fetch_market_data()
        return data