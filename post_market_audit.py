"""
Post-Market Signal Funnel Audit

Traces, for every trading cycle in a saved session log:

  1. Was a CORE signal generated at all (BUY CALL / BUY PUT), based
     purely on EMA/RSI/PCR -- before any downstream filter?
  2. If yes, did it survive VWAP confirmation?
  3. Did it survive the contra-trend block?
  4. Was a trade actually EXECUTED, or was it missed because:
       - a position was already open (duplicate-trade protection)
       - order placement failed (e.g. insufficient balance)

End-of-day summary answers exactly:
  "Kitne BUY CE / BUY PUT signals bane, aur kitne miss hue (aur kyun)"

Usage:
    python post_market_audit.py logs/session_20260819.txt

Requires the session to have been captured via output redirection,
e.g.:
    python main.py 2>&1 | Tee-Object -FilePath "logs\\session_YYYYMMDD.txt"

Also requires the updated core/bot.py that prints the
"Core Signal (pre-filters) : ..." marker line.
"""

import sys
import re


CYCLE_START_MARKER = "Running Trading Cycle..."


def split_into_cycles(text):

    parts = text.split(CYCLE_START_MARKER)

    return parts[1:]


def extract_field(pattern, text, default="N/A"):

    match = re.search(pattern, text)

    if match:
        return match.group(1).strip()

    return default


def analyze_cycle(cycle_text):
    """
    Returns a dict describing what happened in this one cycle.
    """

    result = {
        "close_price": extract_field(r"Close Price\s*:\s*([\d.]+)", cycle_text),
        "pcr": extract_field(r"PCR\s*:\s*([\d.]+)", cycle_text),
        "core_signal": None,
        "final_signal": None,
        "blocked_by": None,
        "executed": False,
    }

    # ==========================================
    # Pre-signal hard blocks (core signal never even evaluated)
    # ==========================================

    if "Market is Choppy" in cycle_text:
        result["core_signal"] = "NOT EVALUATED"
        result["blocked_by"] = "CHOPPY"
        return result

    # FIX (2026-08-31 loss review): new hard block added alongside
    # CHOPPY in bot.py (see config/settings.py's ADX_EXHAUSTION_THRESHOLD)
    # -- without this branch, cycles blocked here would fall through to
    # "UNKNOWN (upgrade bot.py / re-check log)" below since they never
    # reach the "Core Signal" print.
    if "Market is Trend Exhaustion" in cycle_text:
        result["core_signal"] = "NOT EVALUATED"
        result["blocked_by"] = "TREND_EXHAUSTION"
        return result

    if "Insufficient Confluence" in cycle_text:
        result["core_signal"] = "NOT EVALUATED"
        result["blocked_by"] = "CONFLUENCE"
        return result

    # ==========================================
    # Core signal (EMA/RSI/PCR only)
    # ==========================================

    core_match = re.search(r"Core Signal \(pre-filters\)\s*:\s*(.+)", cycle_text)

    if not core_match:
        # Log predates the "Core Signal" marker fix, or cycle ended
        # before reaching this line for some other reason.
        result["core_signal"] = "UNKNOWN (upgrade bot.py / re-check log)"
        return result

    core_signal = core_match.group(1).strip()
    result["core_signal"] = core_signal

    if core_signal == "NO TRADE":
        result["final_signal"] = "NO TRADE"
        result["blocked_by"] = "CORE_SIGNAL (EMA/RSI/PCR didn't align)"
        return result

    # From here on, core_signal is BUY CALL or BUY PUT

    if "VWAP Confirmation Failed" in cycle_text:
        result["final_signal"] = "NO TRADE"
        result["blocked_by"] = "VWAP"
        return result

    if "blocked (" in cycle_text:
        result["final_signal"] = "NO TRADE"
        result["blocked_by"] = "TREND_FILTER"
        return result

    # Passed VWAP + trend filter -> check what actually happened next

    final_match = re.search(r"Final Signal\s*:\s*(.+)", cycle_text)
    result["final_signal"] = (
        final_match.group(1).strip() if final_match else core_signal
    )

    if "Trade Already Open" in cycle_text:
        result["blocked_by"] = "ALREADY_IN_POSITION"
        return result

    if "Order Placement Failed" in cycle_text:
        result["blocked_by"] = "ORDER_FAILED"
        return result

    if "PAPER TRADE" in cycle_text or "ACTIVE POSITION" in cycle_text:
        result["executed"] = True
        return result

    result["blocked_by"] = "UNKNOWN (could not confirm execution)"
    return result


def read_log_file(path):
    """
    FIX: PowerShell's Tee-Object writes files in UTF-16 encoding by
    default on Windows PowerShell 5.1 (not UTF-8). Assuming UTF-8
    unconditionally silently produced garbled/empty-looking content
    (via errors="ignore"), so "Running Trading Cycle..." never
    matched anything and every count came back 0.

    Tries several encodings and picks whichever one actually contains
    our marker text.
    """

    for enc in ("utf-8-sig", "utf-16", "utf-8", "cp1252", "latin-1"):

        try:
            with open(path, "r", encoding=enc) as f:
                content = f.read()
        except (UnicodeError, UnicodeDecodeError):
            continue

        if "Running Trading Cycle" in content:
            return content

    # Last resort: return whatever utf-8 (lossy) gives, so the script
    # doesn't crash outright even if nothing matched above.
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def main():

    if len(sys.argv) < 2:
        print("Usage: python post_market_audit.py <path_to_log_file>")
        sys.exit(1)

    log_path = sys.argv[1]

    text = read_log_file(log_path)

    cycles = split_into_cycles(text)

    print("=" * 70)
    print(f"SIGNAL FUNNEL AUDIT - {log_path}")
    print("=" * 70)
    print(f"Total Cycles Run : {len(cycles)}")
    print("=" * 70)

    core_call_count = 0
    core_put_count = 0
    executed_call = 0
    executed_put = 0
    missed_reasons = {}

    for i, cycle in enumerate(cycles, start=1):

        r = analyze_cycle(cycle)

        print(f"\nCycle {i}  |  Close: {r['close_price']}  |  PCR: {r['pcr']}")
        print(f"  Core Signal   : {r['core_signal']}")
        print(f"  Final Signal  : {r['final_signal']}")
        print(f"  Executed      : {r['executed']}")

        if r["blocked_by"]:
            print(f"  Blocked By    : {r['blocked_by']}")
            missed_reasons[r["blocked_by"]] = missed_reasons.get(r["blocked_by"], 0) + 1

        if r["core_signal"] == "BUY CALL":
            core_call_count += 1
            if r["executed"]:
                executed_call += 1

        elif r["core_signal"] == "BUY PUT":
            core_put_count += 1
            if r["executed"]:
                executed_put += 1

    print("\n" + "=" * 70)
    print("END-OF-DAY SIGNAL FUNNEL SUMMARY")
    print("=" * 70)

    print(f"\nCore BUY CALL signals generated : {core_call_count}")
    print(f"  -> Executed as trades          : {executed_call}")
    print(f"  -> Missed                      : {core_call_count - executed_call}")

    print(f"\nCore BUY PUT signals generated  : {core_put_count}")
    print(f"  -> Executed as trades          : {executed_put}")
    print(f"  -> Missed                      : {core_put_count - executed_put}")

    total_core = core_call_count + core_put_count
    total_executed = executed_call + executed_put

    print(f"\nTOTAL core signals (CE+PE)      : {total_core}")
    print(f"TOTAL executed                  : {total_executed}")
    print(f"TOTAL missed                    : {total_core - total_executed}")

    print("\n" + "-" * 70)
    print("Missed / Blocked -- breakdown by reason (across ALL cycles,")
    print("including cycles where no core signal even formed):")
    print("-" * 70)

    for reason, count in sorted(missed_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason:35s} : {count}")

    print("=" * 70)


if __name__ == "__main__":
    main()
