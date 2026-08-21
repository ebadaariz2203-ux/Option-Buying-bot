import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from paper_trade.paper_trade import (
    execute_paper_trade,
    save_trade,
    close_paper_trade,
)





print("\n========== PAPER CLOSE TEST ==========")

# =================================
# Fake trade
# =================================

trade = {
    "OrderID": "TEST-CLOSE-001",
    "Entry": 100.0,
    "Target": 120.0,
    "StopLoss": 90.0,

    "ATR": 10.0,
    "ATRMultiplier": 1.5,
    "RiskReward": 2.0,

    "Strike": 25000,
    "OptionType": "CE",

    "Quantity": 75,
}

# =================================
# Execute / OPEN trade
# =================================

trade_data = execute_paper_trade(
    "BUY CALL",
    trade
)

if trade_data is None:
    print("TEST FAILED: Could not open trade.")
    raise SystemExit

print("\nTEST OPEN SUCCESS")

print(trade_data)

# =================================
# Save OPEN trade
# =================================

save_trade(trade_data)

print("\nOPEN trade saved.")

# =================================
# CLOSE trade
# Fake exit = 120
# =================================

trade_data["Exit"] = 120.0
trade_data["PnL"] = 1500.0
trade_data["PnLPercent"] = 20.0
trade_data["ExitReason"] = "TEST EXIT"

result = close_paper_trade(
    trade_data,
    120.0,
    "TEST EXIT"
)

print("\n========== TEST RESULT ==========")
print(result)
print("==================================")