from datetime import datetime
from zoneinfo import ZoneInfo
import csv
import os

from logger.logger import logger

from portfolio.portfolio_manager import (
    lock_capital,
    unlock_capital,
    update_balance,
)

from config.settings import LAST_TRADE_FORCE_EXIT_TIME

# FIX: this cost-model engine existed in the repo but had zero callers
# -- close_paper_trade() computed final_pnl as a raw premium delta with
# no brokerage/STT/GST/slippage deducted, overstating every reported
# P&L versus what live trading would actually return.
from execution.slippage import apply_slippage
from execution.charges import calculate_charges


def is_eod_exit_time():
    """
    Returns True when intraday EOD exit time is reached.
    Indian market time: Asia/Kolkata

    FIX: previously hardcoded exit_hour=15, exit_minute=20 here,
    completely separate from settings.py's LAST_TRADE_FORCE_EXIT_TIME
    ("15:10"). Two different EOD cutoffs existed in the system at
    once (15:10 vs 15:20) that could silently disagree. Now this
    reads the same setting bot.py's "LAST TRADE FORCE EXIT" block
    uses, so there is exactly one EOD cutoff time everywhere.
    """

    now = datetime.now(
        ZoneInfo("Asia/Kolkata")
    )

    exit_hour, exit_minute = map(
        int, LAST_TRADE_FORCE_EXIT_TIME.split(":")
    )

    if (
        now.hour > exit_hour
        or (
            now.hour == exit_hour
            and now.minute >= exit_minute
        )
    ):
        return True

    return False


def close_paper_trade(
    trade,
    exit_price,
    exit_reason,
    realized_pnl=0.0,
):
    """
    Close the remaining quantity of a paper trade.

    Partial exit P&L is passed through realized_pnl.
    Final P&L is calculated only for the remaining quantity.

    Total P&L =
        Partial Realized P&L
        +
        Final Remaining-Quantity P&L
    """

    try:

        entry_price = float(trade["Entry"])
        exit_price = float(exit_price)
        remaining_qty = int(trade["Quantity"])

        realized_pnl = round(float(realized_pnl), 2)

        # ==========================================
        # FINAL P&L OF REMAINING QUANTITY
        #
        # FIX: apply realistic exit slippage and brokerage/STT/GST
        # charges (execution/) to this leg instead of a raw premium
        # delta, so reported P&L reflects what a live fill would
        # actually net. exit_price itself (used for "Exit"/"ExitPrice"
        # below and shown to the user) stays the quoted LTP -- only the
        # P&L math accounts for the fill cost.
        # ==========================================

        actual_exit_price = apply_slippage(exit_price, "SELL")

        charges = calculate_charges(
            entry_price, actual_exit_price, remaining_qty
        )

        final_pnl = round(
            (actual_exit_price - entry_price) * remaining_qty
            - charges["TotalCharges"],
            2
        )

        # ==========================================
        # TOTAL TRADE P&L
        # ==========================================

        total_pnl = round(
            realized_pnl + final_pnl,
            2
        )

        # ==========================================
        # P&L PERCENTAGE
        #
        # Calculate against original trade value
        # ==========================================

        original_quantity = int(
            trade.get(
                "OriginalQuantity",
                remaining_qty
            )
        )

        original_trade_value = round(
            entry_price * original_quantity,
            2
        )

        if original_trade_value > 0:

            pnl_percent = round(
                (total_pnl / original_trade_value) * 100,
                2
            )

        else:

            pnl_percent = 0.0

        # ==========================================
        # CAPITAL UNLOCK
        #
        # Only remaining quantity is still locked.
        # Partial quantity has already been exited
        # logically and is therefore not included here.
        # ==========================================

        remaining_trade_value = round(
            entry_price * remaining_qty,
            2
        )

        unlock_capital(remaining_trade_value)

        # ==========================================
        # UPDATE BALANCE
        # ==========================================

        update_balance(total_pnl)

        # ==========================================
        # UPDATE TRADE
        # ==========================================

        trade["Exit"] = exit_price
        trade["ExitPrice"] = exit_price

        trade["Status"] = "CLOSED"

        trade["ExitReason"] = exit_reason

        trade["PartialPnL"] = realized_pnl
        trade["FinalPnL"] = final_pnl
        trade["Charges"] = charges["TotalCharges"]
        trade["PnL"] = total_pnl
        trade["PnLPercent"] = pnl_percent

        # ==========================================
        # REMOVE FROM OPEN TRADES
        # ==========================================

        remove_open_trade(trade)

        # ==========================================
        # RESULT
        # ==========================================

        return {
            "Status": "CLOSED",
            "ExitPrice": exit_price,
            "ExitReason": exit_reason,

            "PartialPnL": realized_pnl,
            "FinalPnL": final_pnl,
            "Charges": charges["TotalCharges"],

            "PnL": total_pnl,
            "PnLPercent": pnl_percent,
        }

    except Exception as e:

        # NOTE: core/bot.py's monitor_open_trade() now checks for this
        # None return on every exit path and retries closing next tick
        # instead of assuming the position is closed -- see the
        # "CLOSE FAILED" handling there.
        print(
            f"[CLOSE PAPER TRADE ERROR] {e}"
        )
        logger.error(f"close_paper_trade() failed: {e}")

        return None


def execute_paper_trade(signal, trade):

    trade_value = trade["Entry"] * trade["Quantity"]

    if not lock_capital(trade_value):

        print("Insufficient Balance")
        return None

    trade_data = {

        "OrderID": trade.get("OrderID", ""),

        "Timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "Time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "Signal": signal,

        "Status": "OPEN",

        "Entry": trade["Entry"],

        "Target": trade["Target"],

        "StopLoss": trade["StopLoss"],

        "ATR": trade.get("ATR", 0),

        "ATRMultiplier": trade.get(
            "ATRMultiplier", 0
        ),

        "RiskReward": trade.get(
            "RiskReward", 0
        ),

        "Strike": trade.get(
            "Strike", 0
        ),

        "OptionType": trade.get(
            "OptionType", ""
        ),

        "Quantity": trade.get(
            "Quantity", 0
        ),

        "PnL": ""
    }
    return trade_data


def save_trade(trade_data):

    file_name = "trade_history/open_positions.csv"
    file_exists = os.path.isfile(file_name)

    # FIX: added "Symbol", "OriginalQuantity", "PartialBooked" to the
    # persisted fields. These were previously silently dropped
    # (extrasaction="ignore") because they weren't in this list -
    # which meant that if the bot ever crashed/restarted while a
    # trade was open, there was no way to recover it: "Symbol" is
    # required for live LTP monitoring, and without it a recovered
    # trade could only fall back to a stale Entry price forever.
    with open(file_name, mode="a", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "OrderID",
                "Timestamp",
                "Time",
                "Signal",
                "Status",
                "Entry",
                "Target",
                "StopLoss",
                "ATR",
                "ATRMultiplier",
                "RiskReward",
                "Risk",
                "Strike",
                "OptionType",
                "Symbol",
                "Quantity",
                "OriginalQuantity",
                "PartialBooked",
                "PnL"
            ],
            extrasaction="ignore",
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(trade_data)


def load_open_trade():
    """
    NEW FUNCTION — Crash recovery.

    On bot startup, checks trade_history/open_positions.csv for a
    position that was never closed (i.e. the bot crashed or was
    killed while a trade was open, so remove_open_trade() never ran
    to clear its row).

    If found, returns it as a dict ready to hand to
    PositionManager.open_position() so monitor_open_trade() can
    resume tracking it — instead of the position being silently
    orphaned (still "open" on disk, but nothing in memory watching
    it, capital never unlocked, outcome never recorded).

    Returns None if there's no open position, or if more than 1 row
    is found (shouldn't happen given this bot's single-position
    design — in that case we deliberately do NOT guess which one is
    real; it's flagged for manual reconciliation instead).
    """

    file_name = "trade_history/open_positions.csv"

    if not os.path.exists(file_name):
        return None

    with open(file_name, "r", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        return None

    if len(rows) > 1:
        print(
            f"\n[RECOVERY WARNING] {len(rows)} rows found in "
            f"open_positions.csv — expected at most 1 for this bot's "
            f"single-position design. NOT auto-recovering to avoid "
            f"guessing wrong. Please reconcile open_positions.csv "
            f"manually, then restart."
        )
        return None

    row = rows[0]

    try:

        quantity = int(float(row.get("Quantity", 0) or 0))

        original_quantity_raw = (
            row.get("OriginalQuantity") or row.get("Quantity", 0)
        )

        trade = {
            "OrderID": row.get("OrderID", ""),
            "Timestamp": row.get("Timestamp", ""),
            "Time": row.get("Time", ""),
            "Signal": row.get("Signal", ""),
            "Status": row.get("Status", "FILLED"),
            "Entry": float(row["Entry"]),
            "Target": float(row["Target"]),
            "StopLoss": float(row["StopLoss"]),
            "ATR": float(row.get("ATR", 0) or 0),
            "ATRMultiplier": float(row.get("ATRMultiplier", 0) or 0),
            "RiskReward": float(row.get("RiskReward", 0) or 0),
            "Risk": float(row.get("Risk", 0) or 0),
            "Strike": float(row.get("Strike", 0) or 0),
            "OptionType": row.get("OptionType", ""),
            "Symbol": row.get("Symbol", ""),
            "Quantity": quantity,
            "OriginalQuantity": int(float(original_quantity_raw or 0)),
            "PartialBooked": (
                str(row.get("PartialBooked", "False")).strip().lower()
                == "true"
            ),
            "PnL": "",
        }

    except (KeyError, ValueError) as e:

        print(f"\n[RECOVERY WARNING] Could not parse open_positions.csv row: {e}")
        return None

    if not trade["Symbol"]:

        print(
            "\n[RECOVERY WARNING] Recovered position has no Symbol "
            "stored (likely saved before this fix was applied). "
            "Live LTP monitoring will fall back to the Entry price "
            "for this trade until it closes."
        )

    return trade


def remove_open_trade(trade):
    """
    Remove a closed trade from open_positions.csv.
    """

    file_name = "trade_history/open_positions.csv"

    if not os.path.exists(file_name):
        return

    with open(file_name, "r", newline="") as file:

        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not fieldnames:
        return

    remaining_rows = []
    removed = False

    trade_order_id = str(
        trade.get("OrderID", "")
    ).strip()

    trade_time = str(
        trade.get("Time", "")
    ).strip()

    for row in rows:

        row_order_id = str(
            row.get("OrderID", "")
        ).strip()

        row_time = str(
            row.get("Time", "")
        ).strip()

        same_trade = (
            row_order_id == trade_order_id
            and
            row_time == trade_time
        )

        if same_trade:
            removed = True
            continue

        # Remove unexpected CSV fields
        clean_row = {
            field: row.get(field, "")
            for field in fieldnames
        }

        remaining_rows.append(clean_row)

    with open(file_name, "w", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(remaining_rows)

    if removed:
        print(
            "[OPEN POSITIONS] "
            "Closed trade removed successfully."
        )
    else:
        print(
            "[OPEN POSITIONS] "
            "Trade not found."
        )


def monitor_trade(current_price, trade):
    """
    Monitor paper trade status.

    Before partial booking:
        Target + Stop Loss are active.

    After partial booking:
        Only Stop Loss remains active.
    """

    # =================================
    # PARTIAL PROFIT ALREADY BOOKED
    # =================================

    if trade.get("PartialBooked", False):

        if current_price <= trade["StopLoss"]:
            return "STOP LOSS HIT"

        return "OPEN"

    # =================================
    # NORMAL TRADE
    # =================================

    if current_price >= trade["Target"]:
        return "TARGET HIT"

    elif current_price <= trade["StopLoss"]:
        return "STOP LOSS HIT"

    return "OPEN"
