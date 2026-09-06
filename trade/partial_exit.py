"""
Partial Profit Booking Engine
"""

from config.settings import PARTIAL_EXIT_PERCENT


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
    """

    if exit_percent is None:
        exit_percent = PARTIAL_EXIT_PERCENT

    exit_quantity = int(
        quantity * exit_percent / 100
    )


    remaining_quantity = (
        quantity - exit_quantity
    )


    return (
        exit_quantity,
        remaining_quantity
    )