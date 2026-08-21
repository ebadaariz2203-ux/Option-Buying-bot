"""
Corrected LTP test - fetches a REAL tradingsymbol from the option
chain first (instead of guessing one), then tests get_ltp() on it.
"""

from market_data.kite_provider import KiteProvider

provider = KiteProvider()

# Get current spot to build the option chain
spot_data = provider.get_market_data()
spot_price = float(spot_data.iloc[-1]["Close"])

print(f"Spot Price: {spot_price}")

option_chain = provider.get_option_chain(spot_price)

# Pick the ATM Call strike from the real chain
atm_strike = option_chain["ATM_Strike"]

atm_call = next(
    s for s in option_chain["Strikes"]
    if s["Strike"] == atm_strike and s["Type"] == "CE"
)

real_symbol = atm_call["Symbol"]

print(f"\nUsing real Symbol from option chain: {real_symbol}")
print(f"LTP from option chain data           : {atm_call['LTP']}")

# Now test get_ltp() with the real symbol
price = provider.get_ltp(real_symbol)

print(f"LTP from get_ltp() live fetch         : {price}")

if abs(price - atm_call["LTP"]) < 5:
    print("\n[PASS] get_ltp() returned a consistent, real price.")
else:
    print("\n[WARN] Prices differ noticeably - check if this is "
          "expected (e.g. price moved between the two calls) or a bug.")
