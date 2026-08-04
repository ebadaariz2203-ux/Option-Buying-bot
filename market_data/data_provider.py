from abc import ABC, abstractmethod


class DataProvider(ABC):

    @abstractmethod
    def get_market_data(self):
        """
        Fetch market OHLCV data.
        """
        pass

    @abstractmethod
    def get_option_chain(self, spot_price):
        """
        Fetch option chain.
        """
        pass