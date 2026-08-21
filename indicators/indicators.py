import pandas as pd
import numpy as np

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
def calculate_adx(data, period=14):
    """
    Calculate Average Directional Index (ADX)

    Required Columns:
    High
    Low
    Close
    """

    df = data.copy()

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    # Directional Movement
    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm = plus_dm.where(
        (plus_dm > minus_dm) & (plus_dm > 0),
        0
    )

    minus_dm = minus_dm.where(
        (minus_dm > plus_dm) & (minus_dm > 0),
        0
    )

    # True Range
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    dx = (
        (plus_di - minus_di).abs()
        / (plus_di + minus_di)
    ) * 100
    adx = dx.rolling(period).mean()

    data["ADX"] = adx

    return data
    

def calculate_vwap(data):
    """
    Calculate session VWAP using valid volume.

    VWAP = cumulative(Typical Price × Volume)
           / cumulative(Volume)
    """

    data = data.copy()

    typical_price = (
        data["High"]
        + data["Low"]
        + data["Close"]
    ) / 3

    volume = pd.to_numeric(
        data["Volume"],
        errors="coerce"
    ).fillna(0)

    cumulative_volume = volume.cumsum()

    cumulative_tp_volume = (
        typical_price * volume
    ).cumsum()

    data["VWAP"] = (
        cumulative_tp_volume /
        cumulative_volume.replace(0, float("nan"))
    )

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
def get_trend(data):
    """
    Determine market trend using EMA 20 and EMA 50.
    Returns:
        UPTREND
        DOWNTREND
        SIDEWAYS
    """

    # Make sure EMAs exist
    if "EMA_20" not in data.columns:
        data = calculate_ema(data, 20)

    if "EMA_50" not in data.columns:
        data = calculate_ema(data, 50)

    ema20 = data["EMA_20"].iloc[-1]
    ema50 = data["EMA_50"].iloc[-1]

    if ema20 > ema50:
        return "UPTREND"
    elif ema20 < ema50:
        return "DOWNTREND"
    else:
        return "SIDEWAYS"
