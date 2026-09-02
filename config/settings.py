BROKER = "PAPER"
BOT_NAME = "Option Buying Bot"
VERSION = "1.0"
PAPER_TRADING = True

# ===============================
# TRADE ENTRY WINDOW
# ===============================

TRADE_ENTRY_START_TIME = "09:30"
NO_NEW_ENTRY_AFTER = "14:45"

# ===============================
# LAST TRADE FORCE EXIT
# ===============================
# FIX (dedup): this used to be defined twice in this file (once near
# the top, once near the bottom) with identical values - harmless but
# confusing. Now defined once.
#
# This is also the single source of truth for end-of-day exit time -
# paper_trade.py's is_eod_exit_time() now reads this value instead of
# its own separate hardcoded 15:20, so there's only one EOD cutoff in
# the whole system instead of two different ones (15:10 here vs 15:20
# there) that could silently disagree.

LAST_ENTRY_WINDOW_START_TIME = "14:45"
LAST_TRADE_FORCE_EXIT_TIME = "15:10"

ATR_MULTIPLIER = 1.0
RISK_REWARD = 2

CAPITAL = 50000
RISK_PER_TRADE = 3
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

# FIX (2026-08-31 loss review): a BUY PUT was taken at ADX=72.45 (very
# strong) with ATR Expanding=False, EMA Gap=15.68 -> passed confluence
# as "Strong Trend" + "HTF Confirmed" (2/2) since strong_trend only
# looks at the EMA20/50 gap, not ADX or ATR expansion. The premium then
# whipsawed in a ~9-point range for the full 45-minute hold (nowhere
# near the ATR-based target) and the time exit closed it at -131.22.
#
# A very high ADX reading combined with a NON-expanding ATR is a known
# trend-exhaustion pattern (the move has already happened; ADX is a
# lagging indicator and stays elevated after momentum has stalled)
# rather than a fresh trending opportunity. detect_market_regime() now
# labels this combination "TREND EXHAUSTION" and bot.py hard-blocks it
# alongside CHOPPY -- this is a narrow, evidence-based safety gate
# (like the CHOPPY block), not a general re-tightening of the
# confluence AND-chain, so normal trending/weak-trend days are
# unaffected.
ADX_EXHAUSTION_THRESHOLD = 65

TRADE_MONITOR_INTERVAL = 1

# ===============================
# TIME BASED EXIT
# ===============================
# Force-closes an open trade after MAX_HOLDING_MINUTES regardless of
# Target/StopLoss, to cap theta-decay exposure on positions that
# aren't moving favorably.

TIME_EXIT_ENABLE = True
MAX_HOLDING_MINUTES = 45

# ===============================
# LIVE PRICE FALLBACK
# ===============================
# How many seconds a cached LTP is trusted for if a fresh live fetch
# fails. Beyond this, get_live_premium() returns None for that tick
# (force-exit checks still run using the last known price - see the
# FIX comment in bot.py's monitor_open_trade()).

LTP_MAX_STALE_SECONDS = 10

# ===============================
# NEW: Signal Confluence
# ===============================
# generate_trading_signal() in bot.py still stacks several confirmation
# checks (strong_trend, higher-timeframe match, atr_expanding) on top
# of the core EMA/RSI/PCR signal, VWAP confirmation, and the
# contra-trend block. Those last two (VWAP, contra-trend) remain hard
# requirements since they confirm DIRECTION, not just trend "quality".
#
# strong_trend, HTF-match and (as of 2026-08-31) atr_expanding are
# scored instead of all being a hard AND. SIGNAL_CONFIRMATIONS_REQUIRED
# controls how many of these 3 must pass:
#   3 = strict (ALL required, closest to the original 2-of-2 behaviour
#       now that a 3rd factor exists).
#   2 = default. Net effect vs. the old 2-of-2 strong_trend+HTF check:
#       PURELY ADDITIVE -- anything that passed before (both
#       strong_trend AND htf_confirmed true) still passes regardless of
#       atr_expanding, but a trade can now ALSO pass when only one of
#       (strong_trend, htf_confirmed) holds as long as atr_expanding is
#       True (real volatility expansion standing in as evidence the
#       move is genuine). Nothing that used to pass is newly blocked.
#   1 = relaxed - only ONE of the 3 needs to pass. Use this if the bot
#       is going multiple sessions with zero trades and logs show these
#       are the checks most often failing.
#
# NOTE: this score is independent of the TREND EXHAUSTION hard block
# (ADX_EXHAUSTION_THRESHOLD above) -- a setup with ADX >= that
# threshold and atr_expanding False is skipped before this score is
# even computed, regardless of what SIGNAL_CONFIRMATIONS_REQUIRED is
# set to.
SIGNAL_CONFIRMATIONS_REQUIRED = 2

# ===============================
# WHIPSAW COOLDOWN
# ===============================
# FIX (2026-09-01 review): on 2026-09-01, two trades (13:55 PUT, 14:30
# PUT) reversed and hit their stop-loss within 1 minute of entry --
# classic whipsaw. The obvious fix ("cooldown after every fast stop")
# was tested against that SAME day's data first and rejected: the
# trade immediately following each of those two fast stops (14:02 PUT,
# 14:36 PUT) was itself a winner (+2352.62 and +402.42) -- a cooldown
# on every single fast stop would have blocked +2755.04 of that day's
# profit while preventing zero losses (a cooldown can only block the
# NEXT trade, not the fast stop that already happened).
#
# So this only triggers after CONSECUTIVE_FAST_STOPS_TRIGGER fast
# stop-losses IN A ROW, in the SAME direction (CALL and PUT tracked
# independently) -- a single fast stop does nothing; a win or a
# slower stop-loss resets that direction's streak back to zero.
WHIPSAW_COOLDOWN_ENABLE = True

# A STOP LOSS HIT exit counts as "fast" (whipsaw-like) only if it was
# also a LOSING trade closed within this many minutes of entry. Keeps
# profitable trailing-stop exits (e.g. a big winner that happens to
# close in a few minutes) from ever counting.
FAST_STOP_HOLD_MINUTES = 3

# How many consecutive fast stop-losses, same direction, before that
# direction's new entries are paused.
CONSECUTIVE_FAST_STOPS_TRIGGER = 2

# How long that direction stays paused once triggered.
WHIPSAW_COOLDOWN_MINUTES = 15

# ===============================
# Backtest
# ===============================

RUN_BACKTEST = False
