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
    

    def run(self):
        data = self.fetch_market_data()
        return data