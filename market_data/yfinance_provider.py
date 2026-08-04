from market_data.data_provider import DataProvider

from market_data.market_data import get_nifty_data

from option_chain.option_data import get_option_chain


class YFinanceProvider(DataProvider):

    def get_market_data(self):

        return get_nifty_data()

    def get_option_chain(self, spot_price):

        return get_option_chain(spot_price)