from market_data.data_provider import DataProvider


class AngelOneProvider(DataProvider):

    def get_market_data(self):

        print("Angel One Market Data")
        raise NotImplementedError("Angel One Market Data not implemented.")

    def get_option_chain(self, spot_price):

        print("Angel One Option Chain")
        raise NotImplementedError("Angel One Option Chain not implemented.")