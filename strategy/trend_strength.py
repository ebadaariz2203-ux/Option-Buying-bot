def trend_strength(data, minimum_gap=5):
    """
    Check EMA20 and EMA50 trend strength.
    """

    ema20 = float(data.iloc[-1]["EMA_20"])
    ema50 = float(data.iloc[-1]["EMA_50"])

    gap = abs(ema20 - ema50)

    if gap >= minimum_gap:
        return True, round(gap, 2)

    return False, round(gap, 2)