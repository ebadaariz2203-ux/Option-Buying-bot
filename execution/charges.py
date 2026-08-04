"""
Charges Calculator

Calculates estimated brokerage and statutory charges
for each completed trade.
"""


def calculate_charges(entry_price, exit_price, quantity):
    """
    Returns estimated total charges.

    Parameters
    ----------
    entry_price : float
    exit_price : float
    quantity : int
    """

    buy_value = entry_price * quantity
    sell_value = exit_price * quantity
    turnover = buy_value + sell_value

    # Brokerage (Paper Trading)
    brokerage = 40.0  # ₹20 Buy + ₹20 Sell

    # Estimated statutory charges
    stt = sell_value * 0.000625
    exchange_charge = turnover * 0.000035
    sebi_charge = turnover * 0.000001
    gst = (brokerage + exchange_charge) * 0.18
    stamp_duty = buy_value * 0.00003

    total = (
        brokerage
        + stt
        + exchange_charge
        + sebi_charge
        + gst
        + stamp_duty
    )

    return {
        "Brokerage": round(brokerage, 2),
        "STT": round(stt, 2),
        "Exchange": round(exchange_charge, 2),
        "SEBI": round(sebi_charge, 2),
        "GST": round(gst, 2),
        "StampDuty": round(stamp_duty, 2),
        "TotalCharges": round(total, 2),
    }