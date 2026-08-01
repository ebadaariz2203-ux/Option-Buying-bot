def simulate_trade(signal, entry, stop_loss, target, future_data):
    """
    Simulate one historical trade.
    """

    for _, candle in future_data.iterrows():

        high = float(candle["High"])
        low = float(candle["Low"])

        if signal == "BUY CALL":

            if high >= target:
                return {
                    "Result": "WIN",
                    "Exit": target,
                }

            if low <= stop_loss:
                return {
                    "Result": "LOSS",
                    "Exit": stop_loss,
                }

        elif signal == "BUY PUT":

            if low <= target:
                return {
                    "Result": "WIN",
                    "Exit": target,
                }

            if high >= stop_loss:
                return {
                    "Result": "LOSS",
                    "Exit": stop_loss,
                }

    if not future_data.empty:

        last_close = float(future_data.iloc[-1]["Close"])

    else:

        last_close = entry

    return {
        "Result": "EOD EXIT",
        "Exit": last_close,
    }