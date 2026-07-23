import pandas as pd


def calculate_ema(data, period=20):

    data[f"EMA_{period}"] = data["Close"].ewm(
        span=period,
        adjust=False
    ).mean()

    return data


def calculate_rsi(data, period=14):

    delta = data["Close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    data["RSI"] = 100 - (100 / (1 + rs))

    return data


def calculate_vwap(data):

    typical_price = (
        data["High"] +
        data["Low"] +
        data["Close"]
    ) / 3

    volume = data["Volume"]

    cumulative_tp_volume = (typical_price * volume).cumsum()
    cumulative_volume = volume.cumsum()

    data["VWAP"] = cumulative_tp_volume / cumulative_volume

    return data

def calculate_volume_average(data, period=20):

    data["Volume_Avg"] = data["Volume"].rolling(period).mean()

    return data

def calculate_atr(data, period=14):

    high = data["High"]
    low = data["Low"]
    close = data["Close"]

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    true_range = tr1.combine(tr2, max)
    true_range = true_range.combine(tr3, max)

    data["ATR"] = true_range.rolling(period).mean()

    return data

