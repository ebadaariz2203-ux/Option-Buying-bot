from indicators.indicators import get_trend


def get_higher_timeframe_trend(data_15m):
    """
    Returns Higher Timeframe Trend.
    """

    return get_trend(data_15m)


def is_higher_timeframe_confirmed(current_trend, higher_trend):
    """
    Returns True if both trends match.
    """

    return current_trend == higher_trend


def detect_market_regime(adx, ema_gap, atr_expanding):
    """
    Detect current market regime.

    Rules:
        ADX >= 25 -> TRENDING
        ADX >= 20 -> WEAK TREND
        ADX < 20  -> CHOPPY
    """

    if adx is None:
        return "CHOPPY"

    if adx >= 25:
        return "TRENDING"

    elif adx >= 20:
        return "WEAK TREND"

    else:
        return "CHOPPY"