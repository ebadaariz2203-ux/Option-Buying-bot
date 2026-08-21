def get_vwap_bias(price, vwap):
    """
    Determine market bias using Futures VWAP.

    Returns:
        BULLISH
        BEARISH
        NO TRADE
    """

    if price is None or vwap is None:
        return "NO TRADE"

    if price > vwap:
        return "BULLISH"

    if price < vwap:
        return "BEARISH"

    return "NO TRADE"


def is_vwap_confirmed(signal, price, vwap):
    """
    Confirm CALL/PUT signal using Futures VWAP.

    BUY CALL  -> Price must be above VWAP
    BUY PUT   -> Price must be below VWAP
    """

    if price is None or vwap is None:
        return False

    if signal == "BUY CALL":
        return price > vwap

    if signal == "BUY PUT":
        return price < vwap

    return False