"""
Dynamic Strike Selector
"""

def get_atm_strike(spot_price):
    """
    Returns nearest 50-point strike.
    """

    strike = int((spot_price + 25) // 50) * 50

    return strike


def select_option(signal, spot_price):
    """
    Returns selected option.
    """

    strike = get_atm_strike(spot_price)

    if signal == "BUY CALL":
        return f"{strike} CE"

    elif signal == "BUY PUT":
        return f"{strike} PE"

def select_best_strike(signal, option_chain):
    """
    Select strike with highest volume.
    """

    if signal == "BUY CALL":
        option_type = "CE"

    elif signal == "BUY PUT":
        option_type = "PE"

    else:
        return None

    strikes = []

    for strike in option_chain["Strikes"]:
        if strike["Type"] == option_type:
            strikes.append(strike)

    # FIX: max() on an empty list raises ValueError. A normal
    # data-provider hiccup (incomplete option chain snapshot with no
    # CE/PE entries of the needed type) used to crash the whole bot
    # here instead of just skipping this trading cycle.
    if not strikes:
        return None

    best = max(strikes, key=lambda x: x["Volume"])

    return best