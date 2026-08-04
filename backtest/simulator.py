from risk.trailing_stop import update_trailing_stop

def simulate_trade(signal, entry, stop_loss, target, future_data):
    """
    Simulate one historical trade.
    """

    for candle_no, (_, candle) in enumerate(future_data.iterrows(), start=1):
        high = float(candle["High"])
        low = float(candle["Low"])
        atr = abs(entry - stop_loss) / 1.5

        if signal == "BUY CALL":

            # Same candle me SL aur Target dono hit
            if low <= stop_loss and high >= target:
                return {
                    "Result": "LOSS",
                    "Exit": stop_loss,
                }

            # Sirf Stop Loss hit
            if low <= stop_loss:
                return {
                    "Result": "LOSS",
                    "Exit": stop_loss,
                    "HoldingCandles": candle_no,

                }

            # Sirf Target hit
            if high >= target:
                return {
                    "Result": "WIN",
                    "Exit": target,
                    "HoldingCandles": candle_no,

                }

        elif signal == "BUY PUT":

            stop_loss = min(
                stop_loss,
                high - (atr * 1.0),
            )

            if low <= target:
                return {
                    "Result": "WIN",
                    "Exit": target,
                    "HoldingCandles": candle_no,

                }

            if high >= stop_loss:
                return {
                    "Result": "LOSS",
                    "Exit": stop_loss,
                    "HoldingCandles": candle_no,

                }

    if not future_data.empty:

        last_close = float(future_data.iloc[-1]["Close"])

    else:

        last_close = entry

    return {
        "Result": "EOD EXIT",
        "Exit": last_close,
        "HoldingCandles": len(future_data),
    }