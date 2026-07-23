import yfinance as yf


def get_nifty_data():

    data = yf.download(
        tickers="^NSEI",
        period="5d",
        interval="5m",
        auto_adjust=False,
        progress=False,
        threads=False
    )

    # Convert MultiIndex columns to normal columns
    if isinstance(data.columns, type(yf.download("^NSEI", period="1d", progress=False).columns)):
        if hasattr(data.columns, "levels"):
            data.columns = data.columns.get_level_values(0)
            if data.empty:
                raise Exception("No market data received. Please check ticker symbol or internet connection.")

    return data