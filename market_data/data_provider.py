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

    def get_ltp(self, tradingsymbol, exchange="NFO"):
        """
        NEW (non-abstract): Fetch the current live premium for a single
        option contract. Kept non-abstract (not @abstractmethod) so
        providers that don't yet support it (YFinance, AngelOne,
        Zerodha stub) don't break at instantiation. Providers that DO
        support live monitoring (KiteProvider) override this.
        """

        raise NotImplementedError(
            f"{self.__class__.__name__} does not support get_ltp()."
        )
