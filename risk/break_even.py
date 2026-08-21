"""
Break Even Stop Loss Engine

FIX: bot.py calls this function passing `trade["Risk"]` (an ABSOLUTE
premium value, e.g. ATR * ATR_MULTIPLIER = ~5-15 rupees) as the 4th
positional argument. The old version of this function treated that
4th argument as `trigger_percent` (expecting a plain percentage like
20), which meant break-even was firing after a tiny, unintended move
(sometimes just 5-10% profit) instead of the intended 1R move.

Now the function correctly interprets the 4th argument as `risk`
(absolute price units) and moves SL to entry only after the price has
moved `trigger_rr` multiples of that risk in profit (default = 1R,
which is standard break-even practice).
"""


def move_to_break_even(
    entry_price,
    current_price,
    stop_loss,
    risk,
    trigger_rr=1.0,
):
    """
    Move Stop Loss to entry price once the trade has moved
    `trigger_rr` x risk (R) in profit.

    entry_price : option premium at entry
    current_price : current option premium
    stop_loss : current stop loss level
    risk : absolute risk per unit used to size the original stop
           loss (e.g. ATR * ATR_MULTIPLIER). Must be > 0.
    trigger_rr : how many R of profit must be reached before moving
                 SL to breakeven (default 1.0 = classic 1R breakeven)
    """

    if risk <= 0:
        return stop_loss

    profit = current_price - entry_price

    if profit >= (risk * trigger_rr):

        if stop_loss < entry_price:
            return entry_price

    return stop_loss
