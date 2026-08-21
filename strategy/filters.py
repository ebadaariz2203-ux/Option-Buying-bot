"""
Market Filters
Contains all price-action based filters.
"""


def bullish_filter(close, ema20, rsi, adx):
    """
    Bullish market confirmation.

    NOTE: RSI threshold relaxed from 60 -> 55 and the ADX>25 gate
    removed from here because market_regime.py / settings.py already
    filter out weak-ADX (choppy) conditions upstream. Keeping ADX>25
    here too meant the trend had to be checked TWICE at the same
    strict bar, which was killing almost every signal.
    """

    return (
        close > ema20
        and rsi > 55
    )


def bearish_filter(close, ema20, rsi, adx):
    """
    Bearish market confirmation.
    """

    return (
        close < ema20
        and rsi < 45
    )


def volume_filter(volume, volume_avg):
    """
    Volume confirmation.
    """

    return volume > volume_avg
