import csv
import os
from datetime import datetime
from zoneinfo import ZoneInfo


# NEW: ExitReason and PnLPercent are appended after the original 11
# columns (not interleaved) so the existing 11 columns' meaning/order
# never changes -- anything reading this file positionally by the old
# 11-column shape still gets the same values in the same positions.
_HEADER = [
    "Date",
    "EntryTime",
    "ExitTime",
    "Signal",
    "Entry",
    "Exit",
    "StopLoss",
    "Target",
    "Status",
    "PnL",
    "Return",
    "ExitReason",
    "PnLPercent",
]


def load_trade_history():

    file_name = "trade_history/trade_history.csv"

    if not os.path.exists(file_name):
        return []

    with open(file_name, "r") as file:

        reader = csv.DictReader(file)

        return list(reader)


def _migrate_header_if_needed(file_name):
    """
    FIX: completed_trade_history.csv already has 38 real paper-trading
    rows written under the old 11-column header (no ExitReason/
    PnLPercent). Rewrites ONLY the header line to the new 13-column
    version so old rows keep loading (csv.DictReader fills missing
    trailing columns with None/blank for short rows) -- the 38 existing
    data rows are never touched, re-parsed, or reformatted. Operates in
    binary mode so the untouched data rows are preserved byte-for-byte
    (this file's existing line endings are already a mix of \\r\\n and
    \\n from prior runs; rewriting the header must not disturb that).
    """

    with open(file_name, "rb") as file:
        content = file.read()

    if not content:
        return

    split_at = content.find(b"\n")
    header_line = content if split_at == -1 else content[:split_at]
    rest = b"" if split_at == -1 else content[split_at + 1:]
    header_line = header_line.rstrip(b"\r")

    current_header = header_line.decode("utf-8").split(",")
    new_header = _HEADER

    if current_header == new_header:
        return  # already migrated

    if current_header != new_header[: len(current_header)]:
        # Unrecognized header shape -- leave the file alone rather than
        # risk corrupting data we don't understand.
        return

    with open(file_name, "wb") as file:
        file.write(",".join(new_header).encode("utf-8") + b"\n" + rest)


def save_trade_history(result):

    file_name = "trade_history/completed_trade_history.csv"
    os.makedirs("trade_history", exist_ok=True)

    file_exists = os.path.exists(file_name) and os.path.getsize(file_name) > 0

    if file_exists:
        _migrate_header_if_needed(file_name)

    # FIX: was naive datetime.now() (whatever timezone the host OS
    # happens to be set to), inconsistent with the IST-aware EntryTime
    # recorded elsewhere in the system (core/bot.py always uses
    # ZoneInfo("Asia/Kolkata")). On a non-IST host this could record an
    # ExitTime that appears to be BEFORE EntryTime, corrupting any
    # analytics keyed on holding time or trade date.
    now = datetime.now(ZoneInfo("Asia/Kolkata"))

    trade_date = now.strftime("%Y-%m-%d")
    exit_time = now.strftime("%H:%M:%S")

    with open(file_name, "a", newline="") as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(_HEADER)

        writer.writerow([
            trade_date,
            result["Time"],
            exit_time,
            result["Signal"],
            result["Entry"],
            result["Exit"],
            result["StopLoss"],
            result["Target"],
            result["Status"],
            result["PnL"],
            result["PnLPercent"],
            result.get("ExitReason", ""),
            result.get("PnLPercent", ""),
        ])
