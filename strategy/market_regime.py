from config.settings import (
    ADX_STRONG_TREND,
    ADX_WEAK_TREND,
    ADX_EXHAUSTION_THRESHOLD,
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

    TREND EXHAUSTION:
        Very high ADX but a NON-expanding ATR -- ADX is a lagging
        indicator, so a reading this high usually reflects a move that
        has already happened rather than one that's still building.
        Without ATR expansion to back it up, this reads as a mature/
        stalling trend at high risk of chopping sideways rather than
        continuing (see the 2026-08-31 loss this was added for).

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
    # TREND EXHAUSTION
    # ==========================================
    # By this point atr_expanding is already known False (the branch
    # above would have caught adx >= 40 with expansion), so this only
    # fires for the specific "very high ADX, flat ATR" combination.

    if (
        adx >= ADX_EXHAUSTION_THRESHOLD
        and not atr_expanding
    ):
        return "TREND EXHAUSTION"

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