"""
Break Even Stop Loss Engine
"""


def move_to_break_even(
    entry_price,
    current_price,
    stop_loss,
    trigger_percent=20
):

    profit_percent = (
        (current_price - entry_price)
        / entry_price
    ) * 100


    if profit_percent >= trigger_percent:

        if stop_loss < entry_price:

            return entry_price


    return stop_loss