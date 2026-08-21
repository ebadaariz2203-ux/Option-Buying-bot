def convert_atr_to_option_premium(
    index_atr,
    delta=0.5,
):
    """
    Convert Nifty ATR
    into Option Premium ATR.
    """

    return round(index_atr * delta, 2)