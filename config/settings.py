BROKER = "PAPER"
BOT_NAME = "Option Buying Bot"
VERSION = "1.0"
PAPER_TRADING = True

ATR_MULTIPLIER = 1.0
RISK_REWARD = 2

CAPITAL = 50000
RISK_PER_TRADE = 2
LOT_SIZE = 75

STRIKE_STEP = 50
STRIKE_OFFSET = 0

DATA_PROVIDER = "KITE"

BREAK_EVEN_ENABLE = True

# NOTE: this now correctly drives risk/break_even.py's `trigger_rr`
# (in units of R, i.e. multiples of the trade's own risk), NOT a raw
# percentage. 1.0 = classic "move SL to entry after 1R profit".
BREAK_EVEN_TRIGGER_RR = 1.0

PARTIAL_EXIT_ENABLE = True

PARTIAL_EXIT_PERCENT = 50

# NEW: Partial exit now triggers once the trade has moved this many
# R-multiples (of its own initial risk) in profit, instead of only at
# the full Target. Full Target (RISK_REWARD = 2, i.e. 2R) was often
# not reached before a reversal gave back the entire unrealized gain
# via the trailing stop. Booking half the position at 1.5R locks in
# profit on strong moves even if price never reaches the full target.
PARTIAL_EXIT_TRIGGER_RR = 1.5

TESTING_MODE = True
# Market session bypass
# False = normal market hours
# True  = allow bot to run outside market hours
BYPASS_MARKET_SESSION = False


# ===============================
# Market Regime Settings — RELAXED
# ===============================
# Old values (ADX_STRONG=25, ADX_WEAK=20, EMA_GAP=15) combined with the
# strategy filters and HTF/VWAP gates made a 5-6 stage AND-chain that was
# almost impossible to pass together -> zero trades for days at a time.
ADX_STRONG_TREND = 22   # was 25
ADX_WEAK_TREND = 15     # was 20
EMA_TREND_GAP = 8       # was 15 (this constant wasn't even being used by
                         # trend_strength() before - see trend_strength.py)
TRADE_MONITOR_INTERVAL = 1

# ===============================
# NEW: Entry Cutoff Time
# ===============================
# Prevents the bot from taking a FRESH trade too close to market
# close. Without this, a signal firing at e.g. 3:25 PM could open a
# brand new position with almost no time to develop before the
# EOD force-exit at 3:20 PM logic in monitor_open_trade() closes it
# again almost immediately.
#
# This only blocks NEW entries — it has no effect on managing/closing
# a trade that's already open (that's handled separately by the EOD
# force-exit check).
NO_NEW_ENTRY_AFTER = "14:45"

# ===============================
# NEW: Signal Confluence
# ===============================
# generate_trading_signal() in bot.py still stacks several confirmation
# checks (strong_trend, higher-timeframe match) on top of the core
# EMA/RSI/PCR signal, VWAP confirmation, and the contra-trend block.
# Those last two (VWAP, contra-trend) remain hard requirements since
# they confirm DIRECTION, not just trend "quality".
#
# strong_trend and HTF-match are now scored instead of both being a
# hard AND. SIGNAL_CONFIRMATIONS_REQUIRED controls how many of these
# 2 must pass:
#   2 = current strict behaviour (BOTH required) - default, no change
#       in behaviour unless you edit this.
#   1 = relaxed - only ONE of (strong_trend, HTF match) needs to pass.
#       Use this if the bot is going multiple sessions with zero
#       trades and you've confirmed via logs that strong_trend/HTF are
#       the checks most often failing.
SIGNAL_CONFIRMATIONS_REQUIRED = 2

# ===============================
# Backtest
# ===============================

RUN_BACKTEST = False
