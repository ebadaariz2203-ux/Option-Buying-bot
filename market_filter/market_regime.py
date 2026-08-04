"""
Market Regime Detection
"""


def detect_market_regime(data):
    """
    Detects current market condition.
    """

    ema20 = data["EMA20"].iloc[-1]
    ema50 = data["EMA50"].iloc[-1]
    atr = data["ATR"].iloc[-1]

    MIN_ATR = 15

    if ema20 > ema50 and atr >= MIN_ATR:
        return "TRENDING"

    return "SIDEWAYS"