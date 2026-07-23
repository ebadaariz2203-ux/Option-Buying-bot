from logger.logger import logger
from market_data.market_data import get_nifty_data
from indicators.indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_volume_average,
    calculate_atr,
)

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

    def run(self):
        data = self.fetch_market_data()
        return data