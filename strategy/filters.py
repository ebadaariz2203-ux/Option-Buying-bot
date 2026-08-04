"""
Market Filters
Contains all price-action based filters.
"""


def bullish_filter(close, ema20, rsi):
    """
    Bullish market confirmation.
    """

    return (
        close > ema20
        and rsi > 60
    )


def bearish_filter(close, ema20, rsi):
    """
    Bearish market confirmation.
    """

    return (
        close < ema20
        and rsi < 40
    )
def volume_filter(volume, volume_avg):
    """
    Volume confirmation.
    """

    return volume > volume_avg