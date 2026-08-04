"""
Trailing Stop Loss Engine
"""


def update_trailing_stop(
    current_price,
    current_stop_loss,
    atr,
    multiplier=1.0,
):
    """
    Move Stop Loss upward for BUY trades.
    """

    new_stop = current_price - (atr * multiplier)

    if new_stop > current_stop_loss:
        return round(new_stop, 2)

    return current_stop_loss