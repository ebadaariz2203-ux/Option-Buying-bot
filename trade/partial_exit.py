"""
Partial Profit Booking Engine
"""


def calculate_partial_exit(
    quantity,
    exit_percent=50
):
    """
    Calculate quantity to book.
    """

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