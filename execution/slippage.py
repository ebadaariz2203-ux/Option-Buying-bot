

"""
Slippage Engine

Applies realistic slippage on entry and exit prices.
"""


def apply_slippage(price, signal, slippage_percent=0.05):
    """
    price : market price

    signal:
        BUY CALL
        BUY PUT
        SELL

    slippage_percent:
        Default = 0.05%

    Returns adjusted execution price.
    """

    slippage = price * (slippage_percent / 100)

    # Buying becomes slightly expensive
    if signal in ["BUY CALL", "BUY PUT"]:
        return round(price + slippage, 2)

    # Selling gets slightly lower price
    elif signal == "SELL":
        return round(price - slippage, 2)

    return round(price, 2)