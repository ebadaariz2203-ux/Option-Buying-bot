"""
Execution Engine

Centralized trade execution.
Future:
- Slippage
- Brokerage
- Live Broker API
- Order Status
"""

from execution.slippage import apply_slippage
from execution.charges import calculate_charges


def execute_trade(entry_price, exit_price, signal, quantity):
    """
    Executes a completed trade.

    Returns execution details.
    """

    actual_entry = apply_slippage(entry_price, signal)

    actual_exit = apply_slippage(exit_price, "SELL")

    gross_pnl = round(
        (actual_exit - actual_entry) * quantity,
        2
    )

    charges = calculate_charges(
        actual_entry,
        actual_exit,
        quantity
    )

    net_pnl = round(
        gross_pnl - charges["TotalCharges"],
        2
    )

    return {
        "Entry": actual_entry,
        "Exit": actual_exit,
        "GrossPnL": gross_pnl,
        "Charges": charges["TotalCharges"],
        "NetPnL": net_pnl,
    }