def simulate_trade(signal, entry, stop_loss, target, future_data):
    """
    Simulate one historical trade.
    """

    for candle_no, (_, candle) in enumerate(future_data.iterrows(), start=1):
        high = float(candle["High"])
        low = float(candle["Low"])

        if signal == "BUY CALL":

            # Same candle me SL aur Target dono hit
            if low <= stop_loss and high >= target:
                return {
                    "Result": "LOSS",
                    "Exit": stop_loss,
                    # FIX: was missing this key. backtest.py reads
                    # result["HoldingCandles"] unconditionally, so this
                    # branch (a same-candle gap/spike hitting both
                    # levels) raised a KeyError and aborted the whole
                    # backtest run.
                    "HoldingCandles": candle_no,
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

            # FIX: this used to recompute stop_loss on every single
            # candle via `min(stop_loss, high - atr)`, regardless of
            # whether price had actually moved favorably -- unlike the
            # BUY CALL branch above, which uses a static stop/target
            # for the whole simulation. In practice this tightened the
            # stop almost immediately on the very first candle (based
            # on nothing but that candle's own high), causing
            # near-instant false stop-outs for BUY PUT backtests
            # regardless of real price action. Mirrored to match the
            # CALL branch's static-level structure instead, including
            # the same-candle-both-hit conservative check.

            # Same candle me SL aur Target dono hit
            if high >= stop_loss and low <= target:
                return {
                    "Result": "LOSS",
                    "Exit": stop_loss,
                    "HoldingCandles": candle_no,
                }

            # Sirf Stop Loss hit
            if high >= stop_loss:
                return {
                    "Result": "LOSS",
                    "Exit": stop_loss,
                    "HoldingCandles": candle_no,

                }

            # Sirf Target hit
            if low <= target:
                return {
                    "Result": "WIN",
                    "Exit": target,
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