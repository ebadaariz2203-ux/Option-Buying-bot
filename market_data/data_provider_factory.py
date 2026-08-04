from market_data.yfinance_provider import YFinanceProvider
from market_data.angelone_provider import AngelOneProvider
from market_data.zerodha_provider import ZerodhaProvider

class DataProviderFactory:

    AVAILABLE_PROVIDERS = (
        "YFINANCE",
        "ANGELONE",
        "ZERODHA",
    )

    @staticmethod
    def create_provider(provider_name):

        provider_name = provider_name.upper().strip()

        if provider_name not in DataProviderFactory.AVAILABLE_PROVIDERS:

            raise ValueError(
                f"""
Unsupported Data Provider : {provider_name}

Available Providers:

- YFINANCE
- ANGELONE
- ZERODHA
"""
            )

        if provider_name == "YFINANCE":
            return YFinanceProvider()

        if provider_name == "ANGELONE":
            return AngelOneProvider()

        if provider_name == "ZERODHA":
            return ZerodhaProvider()

