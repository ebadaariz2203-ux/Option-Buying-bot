def calculate_pnl(entry_price, current_price, quantity):
    """
    Calculate Real-Time Profit & Loss
    """

    pnl = (current_price - entry_price) * quantity

    return round(pnl, 2)
def calculate_return(entry_price, current_price):

    if entry_price == 0:
        return 0

    percentage = (
        (current_price - entry_price)
        / entry_price
    ) * 100

    return round(percentage, 2)
def get_trade_status(
    entry_price,
    current_price,
    quantity,
):
    pnl = calculate_pnl(
        entry_price,
        current_price,
        quantity,
    )

    returns = calculate_return(
        entry_price,
        current_price,
    )

    return {
        "CurrentPrice": current_price,
        "PnL": pnl,
        "Return": returns,
    }