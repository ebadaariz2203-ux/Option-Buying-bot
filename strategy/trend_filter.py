"""
Trend Filter
"""


def get_trend(data):
    """
    Detect market trend using EMA20 and EMA50.
    """

    ema20 = data["EMA_20"].iloc[-1]
    ema50 = data["EMA_50"].iloc[-1]

    if ema20 > ema50:
        return "UPTREND"

    elif ema20 < ema50:
        return "DOWNTREND"

    return "SIDEWAYS"