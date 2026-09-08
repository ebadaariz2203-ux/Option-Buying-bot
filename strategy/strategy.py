from strategy.filters import (
    bullish_filter,
    bearish_filter,
)

from strategy.confirmation import (
    bullish_confirmation,
    bearish_confirmation,
)

from config.settings import (
    BEARISH_RSI_MAX,
    BULLISH_RSI_MIN,
)

def generate_signal(data, option=None, debug=True):
    latest = data.iloc[-1]

    close = float(latest["Close"])
    ema20 = float(latest["EMA_20"])
    rsi = float(latest["RSI"])
    volume = float(latest["Volume"])
    volume_avg = float(latest["Volume_Avg"])
    if option is None:
        pcr = None
    else:
        pcr = float(option["PCR"])


    atr = float(latest["ATR"])
    adx = float(latest["ADX"])

    if debug:

        print("\n========== MARKET ANALYSIS ==========")
        print(f"Close Price : {close:.2f}")
        print(f"EMA 20      : {ema20:.2f}")
        print(f"RSI         : {rsi:.2f}")
        print(f"Volume      : {volume:.0f}")
        print(f"Avg Volume  : {volume_avg:.0f}")
        print(f"PCR         : {pcr}")
        print(f"ATR         : {atr:.2f}")
        print(f"ADX         : {adx:.2f}")
        print("=====================================\n")    

    if debug:

        # NOTE (2026-09-08 fix): these labels used to print fixed 60/40
        # thresholds while bullish_filter/bearish_filter actually
        # checked different numbers (55/45, now BULLISH_RSI_MIN/
        # BEARISH_RSI_MAX via settings.py) -- so a review reading this
        # debug output could see "Condition False" on a trade that the
        # real filter had actually passed. Print the live thresholds
        # instead of hard-coding stale ones.
        print(f"Condition 1 (Close > EMA20): {close > ema20}")
        print(f"Condition 2 (RSI > {BULLISH_RSI_MIN}): {rsi > BULLISH_RSI_MIN}")
        print(f"Condition 3 (Close < EMA20): {close < ema20}")
        print(f"Condition 4 (RSI < {BEARISH_RSI_MAX}): {rsi < BEARISH_RSI_MAX}")

    if debug and pcr is not None:

        print(f"Condition 5 (PCR > 1): {pcr > 1}")
        print(f"Condition 6 (PCR < 1): {pcr < 1}")
        print(f"Condition 7 (ADX > 25): {adx > 25}")   
    if bullish_filter(close, ema20, rsi, adx):

        if bullish_confirmation(pcr):
            return "BUY CALL"

    if bearish_filter(close, ema20, rsi, adx):

        if bearish_confirmation(pcr):
            return "BUY PUT"

    return "NO TRADE"