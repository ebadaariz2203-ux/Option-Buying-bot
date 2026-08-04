from market_data.data_provider import DataProvider


class ZerodhaProvider(DataProvider):

    def get_market_data(self):

        print("Zerodha Market Data")
        raise NotImplementedError("Zerodha Market Data not implemented.")

    def get_option_chain(self, spot_price):

        print("Zerodha Option Chain")
        raise NotImplementedError("Zerodha Option Chain not implemented.")