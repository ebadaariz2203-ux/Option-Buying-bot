"""
Profit Giveback Guard

Break-even (risk/break_even.py) and the ATR trailing stop
(risk/trailing_stop.py) both only engage once profit reaches a full
1R (BREAK_EVEN_TRIGGER_RR / TRAILING_START_TRIGGER_RR) -- see the
2026-09-03 loss review note in config/settings.py for why that gate
exists. But a trade that peaks somewhere below 1R and then fully
reverses gets no protection at all from either mechanism: it rides
all the way back down to its original, un-trailed StopLoss, giving
back 100% of the favorable move it did make plus its full initial
risk (found in the 2026-09-07 loss review: two of that day's three
trades peaked at ~0.5R and ~0.94R, never reached 1R, and both
round-tripped to a full stop-loss).

This guard is independent of break-even/trailing and looks at the
trade's PEAK price (max favorable excursion), not the current price:
once the peak has been at least `trigger_rr` x risk in profit, it
locks in `lock_pct`% of that peak profit by raising the stop to that
level. It only ever raises the stop -- callers should take the max of
this and whatever break-even/trailing already computed -- so once a
trade clears the 1R break-even/trailing threshold, that wider
mechanism naturally takes over.
"""


def apply_giveback_guard(
    entry_price,
    peak_price,
    stop_loss,
    risk,
    trigger_rr=0.5,
    lock_pct=50,
):
    """
    Ratchet the stop loss up to protect part of the best profit a
    trade has seen so far, even if it never reaches the break-even/
    trailing 1R threshold.

    entry_price : option premium at entry
    peak_price  : highest LTP seen so far during this trade's hold
                  (max favorable excursion, tracked per-tick by the
                  caller -- NOT the current price)
    stop_loss   : current stop loss level
    risk        : absolute risk per unit used to size the original
                  stop loss (e.g. ATR * ATR_MULTIPLIER). Must be > 0.
    trigger_rr  : how many R of PEAK profit must have been reached
                  before this guard engages (default 0.5R)
    lock_pct    : percentage of peak profit to lock in once triggered
                  (default 50 = protect half of the best move seen)
    """

    if risk <= 0:
        return stop_loss

    peak_profit = peak_price - entry_price

    if peak_profit < (risk * trigger_rr):
        return stop_loss

    locked_level = entry_price + (peak_profit * lock_pct / 100)

    if locked_level > stop_loss:
        return round(locked_level, 2)

    return stop_loss
