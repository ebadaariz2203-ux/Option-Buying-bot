BROKER = "PAPER"
BOT_NAME = "buying_bot"
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

# ===============================
# TRAILING STOP LOSS
# ===============================
# FIX (2026-09-03 loss review): update_trailing_stop() used to run
# unconditionally on every tick from the moment of entry, ratcheting
# SL to (current_price - ATR_MULTIPLIER x ATR) within seconds of
# entry. Normal intraday option-premium tick noise is comparable in
# size to 1x ATR, so this stopped trades out on ordinary pullbacks
# before any real reversal -- all 4 trades on 2026-09-03 moved
# favorably at some point (one by +10.45, ~1.3R) and still
# round-tripped to a loss or near-breakeven via this trailing stop;
# none exited via target or EOD.
#
# Now: trailing only starts once the trade has reached the same 1R
# profit threshold used for break-even (TRAILING_START_TRIGGER_RR),
# and then trails at a wider distance (TRAILING_ATR_MULTIPLIER, wider
# than the ATR_MULTIPLIER used to size the original stop) so normal
# noise doesn't immediately erase the very move that earned the trail.
TRAILING_START_TRIGGER_RR = BREAK_EVEN_TRIGGER_RR
TRAILING_ATR_MULTIPLIER = 1.5

# ===============================
# GIVEBACK GUARD (2026-09-07 loss review)
# ===============================
# Gap found in break-even/trailing: both only engage once profit
# reaches BREAK_EVEN_TRIGGER_RR/TRAILING_START_TRIGGER_RR (1.0R). Two
# of 2026-09-07's 3 trades reversed from a decent favorable move
# (~0.5R and ~0.94R peak) all the way down to their full original
# StopLoss -- neither ever reached 1R, so break-even/trailing never
# fired and both gave back 100% of the peak move plus the full risk.
#
# This guard is independent of break-even/trailing and engages
# earlier: once PEAK price (not current price) has been at least
# GIVEBACK_GUARD_TRIGGER_RR x risk in profit, ratchet the stop up to
# lock in GIVEBACK_GUARD_LOCK_PCT% of that peak profit. It only ever
# raises the stop (core/bot.py takes the max against the existing
# break-even/trailing stop), so once a trade clears 1R this guard is
# superseded by the wider trailing stop as usual.
#
# Verified against 2026-09-07 tick data before adding: applying this
# retroactively would have raised trade 2's stop to ~69.08 (from a
# fixed 61.46) and trade 3's to ~66.35 (from a fixed 58.23) --
# converting both stop-loss losses (-1492.98, -1323.71) into modest
# gains -- while trade 1 (the winner) would have locked in MORE of its
# 78.00 peak than the eventual time-exit did. 0.5R / 50% are a
# starting point, not re-tuned beyond this one day -- watch a few more
# sessions (or run run_backtest.py) before trusting these numbers.
#
# DISABLED (2026-09-07, later same day): replayed this against 18 real
# trades across 6 sessions (28 Aug - 7 Sep, tick-by-tick from the
# session logs, methodology validated by matching 17/18 replayed PnLs
# exactly against trade_history/completed_trade_history.csv). At these
# defaults it's net NEGATIVE: -1656 across the sample, because it also
# "shakes out" trades that dip early below 1R and then go on to be big
# winners (two 2026-09-01 trades alone lost -2081 and -1642 of upside
# this way) -- a cost that outweighed what it saved on 2026-09-07's 2
# losers. A trigger_rr/lock_pct grid search (0.3-1.25R x 25-75%) came
# back highly non-monotonic/noisy with no stable good region -- a
# sign of overfitting an 18-trade sample, not a real edge. Leaving the
# module and wiring in place (core/bot.py takes max() against
# break-even/trailing either way, so this is inert while disabled) in
# case a less trigger-happy redesign (e.g. requiring the pullback to
# hold for N ticks before locking, not react to a single tick touching
# the trigger) is worth trying later -- do not re-enable with these
# same parameters without new evidence.
GIVEBACK_GUARD_ENABLE = False
GIVEBACK_GUARD_TRIGGER_RR = 0.5
GIVEBACK_GUARD_LOCK_PCT = 50

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
# RSI ENTRY THRESHOLDS
# ===============================
# strategy/filters.py's bearish_filter/bullish_filter used to hard-code
# RSI < 45 (PUT) and RSI > 55 (CALL) -- both just past the neutral 50
# line, so a near-neutral, weak-momentum RSI reading was enough to
# qualify.
#
# 2026-09-08 review: replayed 19 real trades across 5 sessions (31 Aug,
# 1/3/4/8 Sep, tick-by-tick from the session logs, matched 19/19
# against trade_history/completed_trade_history.csv) and correlated
# entry RSI against trade PnL. Both directions agreed: BUY PUT showed
# RSI-vs-PnL correlation -0.36 (n=14) and BUY CALL showed +0.64 (n=5)
# -- i.e. PnL got WORSE the closer entry RSI sat to the old threshold,
# and better the further it was extended in the trade's own direction.
# Concretely, tightening to PUT RSI < 35 / CALL RSI > 58 against that
# same sample would have kept 10 of the 19 trades and turned their net
# PnL from -4871.35 to +1775.95 (win rate 31.6% -> 40.0%).
#
# NOT independently re-validated beyond this one backtest -- CALL n=5
# is far too small to trust on its own; the PUT side (n=14) is thin
# too. Adopted because both signal directions pointed the same way
# (marginal RSI = weak momentum = more whipsaw-prone), which is at
# least a coherent story rather than a single-day fluke. A tighter cut
# (PUT < 30 / CALL > 60) backtested even better (+3690.20 on n=7) but
# was rejected here as almost certainly overfit to 3-4 data points --
# revisit once more sessions have run under these settings.
BEARISH_RSI_MAX = 35    # was 45 (bearish_filter: close < ema20 and rsi < this)
BULLISH_RSI_MIN = 58    # was 55 (bullish_filter: close > ema20 and rsi > this)

# ===============================
# Backtest
# ===============================

RUN_BACKTEST = False
