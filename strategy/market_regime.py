from config.settings import (
    ADX_STRONG_TREND,
    ADX_WEAK_TREND,
    EMA_TREND_GAP
)


def is_atr_expanding(data):

    if len(data) < 6:
        return False

    current_atr = float(
        data.iloc[-1]["ATR"]
    )

    previous_atr = float(
        data.iloc[-6]["ATR"]
    )

    return current_atr > previous_atr


def detect_market_regime(
    adx,
    ema_gap,
    atr_expanding
):
    """
    Detect current market regime.

    TRENDING:
        Strong ADX + sufficient EMA separation
        OR very strong ADX + expanding ATR

    WEAK TREND:
        Moderate ADX + sufficient EMA separation

    CHOPPY:
        Weak ADX and weak EMA separation
    """

    # ==========================================
    # STRONG TREND
    # ==========================================

    if (
        adx >= ADX_STRONG_TREND
        and ema_gap >= EMA_TREND_GAP
        and atr_expanding
    ):
        return "TRENDING"

    # Very strong ADX can confirm trend
    # even when EMA gap is temporarily smaller.

    if (
        adx >= 40
        and atr_expanding
        and ema_gap >= 5
    ):
        return "TRENDING"

    # ==========================================
    # WEAK TREND
    # ==========================================

    if (
        adx >= ADX_WEAK_TREND
        and ema_gap >= 5
    ):
        return "WEAK TREND"

    # ==========================================
    # CHOPPY
    # ==========================================

    return "CHOPPY"