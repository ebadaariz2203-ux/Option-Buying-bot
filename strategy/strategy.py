def generate_signal(data, option):
    latest = data.iloc[-1]

    close = float(latest["Close"])
    ema20 = float(latest["EMA_20"])
    rsi = float(latest["RSI"])
    volume = float(latest["Volume"])
    volume_avg = float(latest["Volume_Avg"])
    pcr = float(option["PCR"])
    atr = float(latest["ATR"])

    print("\n========== MARKET ANALYSIS ==========")
    print(f"Close Price : {close:.2f}")
    print(f"EMA 20      : {ema20:.2f}")
    print(f"RSI         : {rsi:.2f}")
    print(f"Volume      : {volume:.0f}")
    print(f"Avg Volume  : {volume_avg:.0f}")
    print(f"PCR         : {pcr}")
    print(f"ATR         : {atr:.2f}")
    print("=====================================\n")

    # Debug
    print(f"Condition 1 (Close > EMA20): {close > ema20}")
    print(f"Condition 2 (RSI > 60): {rsi > 60}")
    print(f"Condition 3 (Close < EMA20): {close < ema20}")
    print(f"Condition 4 (RSI < 40): {rsi < 40}")
    print(f"Condition 5 (PCR > 1): {pcr > 1}")
    print(f"Condition 6 (PCR < 1): {pcr < 1}")


    if close > ema20 and rsi > 60 and pcr > 1:
        return "BUY CALL"

    elif close < ema20 and rsi < 40 and pcr < 1:
             return "BUY PUT"

    else:
     return "NO TRADE"