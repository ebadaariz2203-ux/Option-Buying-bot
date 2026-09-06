"""
Partial Profit Booking Engine
"""

from config.settings import PARTIAL_EXIT_PERCENT, LOT_SIZE


def calculate_partial_exit(
    quantity,
    exit_percent=None
):
    """
    Calculate quantity to book.

    FIX: exit_percent used to default to a hardcoded 50, completely
    ignoring config/settings.py's PARTIAL_EXIT_PERCENT -- changing that
    setting had no effect anywhere. Now defaults to the actual setting
    (still overridable by passing exit_percent explicitly).

    FIX: exit_quantity used to be a plain int(quantity * pct / 100),
    with no regard for LOT_SIZE -- options only trade in whole lots, so
    e.g. a 1-lot (75) position at 50% used to split into 37/38, neither
    of which is a valid real order size. Now rounds to the nearest
    whole number of lots, and returns (0, quantity) -- i.e. "don't
    partial-exit" -- when the position is too small to split into two
    non-empty lot-aligned pieces (a single lot just rides to full
    target/stop instead).
    """

    if exit_percent is None:
        exit_percent = PARTIAL_EXIT_PERCENT

    if not LOT_SIZE or quantity < 2 * LOT_SIZE:
        return 0, quantity

    total_lots = quantity // LOT_SIZE

    exit_lots = round(total_lots * exit_percent / 100)
    exit_lots = max(1, min(exit_lots, total_lots - 1))

    exit_quantity = exit_lots * LOT_SIZE
    remaining_quantity = quantity - exit_quantity

    return (
        exit_quantity,
        remaining_quantity
    )