from strategy.filters import (
    bullish_filter,
    bearish_filter,
)

from strategy.confirmation import (
    bullish_confirmation,
    bearish_confirmation,
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

    if debug:

        print("\n========== MARKET ANALYSIS ==========")
        print(f"Close Price : {close:.2f}")
        print(f"EMA 20      : {ema20:.2f}")
        print(f"RSI         : {rsi:.2f}")
        print(f"Volume      : {volume:.0f}")
        print(f"Avg Volume  : {volume_avg:.0f}")
        print(f"PCR         : {pcr}")
        print(f"ATR         : {atr:.2f}")
        print("=====================================\n")    

    if debug:

        print(f"Condition 1 (Close > EMA20): {close > ema20}")
        print(f"Condition 2 (RSI > 60): {rsi > 60}")
        print(f"Condition 3 (Close < EMA20): {close < ema20}")
        print(f"Condition 4 (RSI < 40): {rsi < 40}")

    if debug and pcr is not None:

        print(f"Condition 5 (PCR > 1): {pcr > 1}")
        print(f"Condition 6 (PCR < 1): {pcr < 1}")   
    if bullish_filter(close, ema20, rsi):

        if bullish_confirmation(pcr):
            return "BUY CALL"

    if bearish_filter(close, ema20, rsi):

        if bearish_confirmation(pcr):
            return "BUY PUT"

    return "NO TRADE"