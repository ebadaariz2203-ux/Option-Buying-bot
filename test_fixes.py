"""
Pre-Market Test Script

Run this on a market-closed day to sanity-check the fixes before
Monday's live/paper session:

  1. break_even.py logic (standalone, no API needed)
  2. kite_provider.get_ltp() connectivity (needs valid Kite token)
  3. Full signal-generation pipeline on Friday's historical data
     (needs valid Kite token)

Usage:
    python test_fixes.py

You can comment out sections you don't want to run.
"""

import traceback


def test_break_even_logic():

    print("\n" + "=" * 60)
    print("TEST 1: break_even.py logic")
    print("=" * 60)

    from risk.break_even import move_to_break_even

    # Case 1: Not enough profit yet (profit < 1R) -> SL should NOT move
    entry = 150
    current = 155
    stop_loss = 140
    risk = 8  # 1R = 8 rupees

    result = move_to_break_even(entry, current, stop_loss, risk, trigger_rr=1.0)
    expected = 140

    status = "PASS" if result == expected else "FAIL"
    print(f"[{status}] Sub-1R profit (profit=5, risk=8) -> "
          f"SL stays {result} (expected {expected})")

    # Case 2: Exactly 1R profit reached -> SL should move to entry
    current = 158
    result = move_to_break_even(entry, current, stop_loss, risk, trigger_rr=1.0)
    expected = 150

    status = "PASS" if result == expected else "FAIL"
    print(f"[{status}] Exactly 1R profit (profit=8, risk=8) -> "
          f"SL moves to {result} (expected {expected})")

    # Case 3: Well past 1R -> SL should be at entry (not beyond, that's
    # trailing stop's job, not break-even's)
    current = 170
    result = move_to_break_even(entry, current, stop_loss, risk, trigger_rr=1.0)
    expected = 150

    status = "PASS" if result == expected else "FAIL"
    print(f"[{status}] Well past 1R (profit=20, risk=8) -> "
          f"SL at {result} (expected {expected})")

    # Case 4: SL already better than entry -> should NOT move backward
    current = 170
    stop_loss_already_good = 155  # already above entry
    result = move_to_break_even(
        entry, current, stop_loss_already_good, risk, trigger_rr=1.0
    )
    expected = 155

    status = "PASS" if result == expected else "FAIL"
    print(f"[{status}] SL already past entry (155) -> "
          f"stays {result} (expected {expected}, should not move backward)")

    # Case 5: risk = 0 (edge case, avoid divide/logic issues) -> SL unchanged
    result = move_to_break_even(entry, current, stop_loss, risk=0, trigger_rr=1.0)
    expected = stop_loss

    status = "PASS" if result == expected else "FAIL"
    print(f"[{status}] risk=0 edge case -> "
          f"SL stays {result} (expected {expected})")


def test_kite_ltp_connectivity():

    print("\n" + "=" * 60)
    print("TEST 2: kite_provider.get_ltp() connectivity")
    print("=" * 60)

    try:
        from market_data.kite_provider import KiteProvider

        provider = KiteProvider()

        # Replace with any valid current/near-month NIFTY option
        # tradingsymbol you know exists (check via Kite instruments
        # dump or your logs from a previous run's option chain output)
        test_symbol = "NIFTY2582225000CE"  # <-- EDIT THIS

        price = provider.get_ltp(test_symbol)

        print(f"[PASS] LTP for {test_symbol} : {price}")
        print("       (Kite returns last traded/closing price even "
              "on non-trading days, so a valid number here confirms "
              "API connectivity + token validity + symbol format are "
              "all correct.)")

    except Exception as e:
        print(f"[FAIL] get_ltp() raised an exception:")
        print(f"       {e}")
        print("\n       Common causes:")
        print("       - KITE_API_KEY / KITE_ACCESS_TOKEN missing or "
              "expired in .env")
        print("       - tradingsymbol doesn't exist / wrong expiry "
              "format -> edit test_symbol above")
        traceback.print_exc()


def test_full_pipeline_on_historical_data():

    print("\n" + "=" * 60)
    print("TEST 3: Full signal pipeline on last available data")
    print("=" * 60)
    print("(Uses Friday's closing candles - Kite serves historical")
    print(" data even on weekends/holidays)")

    try:
        from core.bot import TradingBot

        bot = TradingBot()

        print("\n--- Fetching market data ---")
        data = bot.fetch_market_data()

        print("\n--- Calculating indicators ---")
        data = bot.calculate_indicators(data)

        print("\n--- Running signal generation (full confluence chain) ---")
        signal, selected_strike = bot.generate_trading_signal(data)

        print("\n" + "-" * 60)
        print(f"RESULT -> Signal: {signal}")

        if selected_strike:
            print(f"          Strike: {selected_strike['Strike']} "
                  f"{selected_strike['Type']}")
            print(f"          Symbol: {selected_strike.get('Symbol', 'MISSING!')}")

            if "Symbol" not in selected_strike or not selected_strike.get("Symbol"):
                print("\n[WARN] 'Symbol' field is missing/empty on the "
                      "selected strike. get_live_premium() will fall "
                      "back to Entry price during monitoring - check "
                      "that kite_provider.py's get_option_chain() is "
                      "the updated version.")
            else:
                print("[PASS] 'Symbol' field present - live LTP "
                      "monitoring will work for this trade.")
        else:
            print("          No strike selected (signal was NO TRADE "
                  "- expected on a day with no fresh intraday move).")

        print("-" * 60)

        print("\n[PASS] Full pipeline ran without crashing.")

    except Exception as e:
        print(f"[FAIL] Pipeline raised an exception:")
        print(f"       {e}")
        traceback.print_exc()


if __name__ == "__main__":

    print("PRE-MARKET TEST SUITE")
    print("Run this before Monday's session to sanity-check the fixes.")

    # Test 1: No API needed, always safe to run
    test_break_even_logic()

    # Test 2 & 3: Need valid Kite API key/token in .env
    # Comment these out if you don't want to hit the API right now
    test_kite_ltp_connectivity()
    test_full_pipeline_on_historical_data()

    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)
