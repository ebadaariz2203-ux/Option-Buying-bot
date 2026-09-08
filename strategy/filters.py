"""
Market Filters
Contains all price-action based filters.
"""

from config.settings import (
    BEARISH_RSI_MAX,
    BULLISH_RSI_MIN,
)


def bullish_filter(close, ema20, rsi, adx):
    """
    Bullish market confirmation.

    NOTE: RSI threshold relaxed from 60 -> 55 and the ADX>25 gate
    removed from here because market_regime.py / settings.py already
    filter out weak-ADX (choppy) conditions upstream. Keeping ADX>25
    here too meant the trend had to be checked TWICE at the same
    strict bar, which was killing almost every signal.

    2026-09-08: threshold moved to config.settings.BULLISH_RSI_MIN
    (55 -> 58) -- a near-neutral RSI just past 55 backtested as the
    weakest of the CALL entries. See settings.py for the analysis.
    """

    return (
        close > ema20
        and rsi > BULLISH_RSI_MIN
    )


def bearish_filter(close, ema20, rsi, adx):
    """
    Bearish market confirmation.

    2026-09-08: threshold moved to config.settings.BEARISH_RSI_MAX
    (45 -> 35) -- a near-neutral RSI just under 45 backtested as the
    weakest of the PUT entries. See settings.py for the analysis.
    """

    return (
        close < ema20
        and rsi < BEARISH_RSI_MAX
    )


def volume_filter(volume, volume_avg):
    """
    Volume confirmation.
    """

    return volume > volume_avg
