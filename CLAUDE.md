# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A NIFTY index-options intraday buying bot (Python). It pulls index/futures candles, computes indicators,
generates a directional signal, sizes and risk-manages a single option position, and either paper-trades
it or routes it to a real broker. There is no test suite in this repo — verify changes by running the bot
in paper mode or via the backtester.

## Commands

```bash
# Run the live/paper bot (reads BROKER/DATA_PROVIDER/PAPER_TRADING from config/settings.py)
python main.py

# Windows: run with UTF-8 console + session logging to logs/session_YYYYMMDD.txt
.\run_bot.ps1          # or run_bot.bat

# Standalone backtest over yfinance-sourced NIFTY data
python run_backtest.py

# One-time-per-day Kite (Zerodha) login: opens browser, exchanges request_token,
# writes KITE_ACCESS_TOKEN into .env
python kite_auto_login.py

# Post-hoc funnel audit of a captured session log (why were signals missed?)
python post_market_audit.py logs/session_YYYYMMDD.txt

# Install deps
pip install -r requirements.txt
```

There is no lint/format/test tooling configured (no pytest/ruff/black config, no CI). Sanity-check changes
by reading bot.py's console output in paper mode (`PAPER_TRADING = True`, `BROKER = "PAPER"`).

## Configuration

- `config/settings.py` holds every tunable (capital, risk %, ATR multiplier, entry/exit time windows,
  which broker/data provider to use, feature toggles). It's listed in `.gitignore` but is currently
  tracked in git anyway (added before the ignore rule) — treat edits to it as real, committed changes,
  not local-only config, unless the user says otherwise.
- Secrets (`KITE_API_KEY`, `KITE_API_SECRET`, `KITE_ACCESS_TOKEN`, AngelOne creds, Telegram bot token) live
  in `.env`, loaded via `python-dotenv`. Never print or commit these.
- All trading-session time logic uses `Asia/Kolkata` (IST) explicitly via `zoneinfo.ZoneInfo` — don't use
  naive `datetime.now()` for anything session/time-window related.

## Architecture

`main.py` sets stdout/stderr to UTF-8 (Windows console defaults to cp1252 and would crash on the
checkmark/emoji output used throughout) and hands off to `core/bot.py`'s `TradingBot`, which is the
central orchestrator — almost everything else is a module it composes:

- **`market_data/`** — one provider class per source (`kite_provider`, `angelone_provider`,
  `zerodha_provider`, `yfinance_provider`), all implementing the `DataProvider` interface
  (`market_data/data_provider.py`). Selected at runtime via `DataProviderFactory` from
  `config.settings.DATA_PROVIDER`. `KiteProvider` is the one actually exercised in live/paper runs;
  the 5-minute signal data and the 15-minute HTF confirmation data are both pulled from the *same*
  provider on purpose (mixing Kite + yfinance previously caused false HTF mismatches).
- **`broker/`** — same factory pattern (`BrokerFactory` from `config.settings.BROKER`): `PaperBroker`
  (simulated fills, the default), `AngelOneBroker`, `ZerodhaBroker`.
- **`indicators/indicators.py`** — EMA/RSI/ATR/ADX/VWAP/volume-average calculations added as columns to
  the OHLC DataFrame.
- **`strategy/`** — signal generation pipeline: `strategy.py` (core EMA/RSI/PCR signal),
  `trend_filter.py` / `trend_strength.py` (trend direction + strength), `mtf_filter.py` (higher-timeframe
  confirmation), `market_regime.py` (TRENDING/CHOPPY classification — CHOPPY is a hard block),
  `vwap_filter.py` (futures VWAP bias confirmation), `strike_selector.py` (picks the option contract).
- **`risk/`** — `atr_converter.py` converts index-ATR to an option-premium ATR; `risk_manager.py` computes
  entry/stop/target (`calculate_trade`); `position_size.py` sizes lots from capital/risk %;
  `trailing_stop.py` and `break_even.py` adjust the stop while a trade is open (break-even trigger is in
  R-multiples of the trade's own initial risk, via `BREAK_EVEN_TRIGGER_RR`, not a raw percentage).
- **`trade/`** — `order_manager.py` (places orders through the broker), `position_manager.py` (tracks the
  single open position, backed by `trade/trade_state.py`), `partial_exit.py`, `pnl_engine.py`,
  `order_history.py`.
- **`paper_trade/`** — `paper_trade.py` (execute/save/monitor/close a simulated trade, EOD exit time
  check), `trade_validator.py` (pre-trade checks, e.g. `EnoughCapital`).
- **`portfolio/portfolio_manager.py`** — running capital/P&L summary.
- **`backtest/`** — `backtest.py` runs the same signal pipeline candle-by-candle over historical data;
  `report.py` writes a timestamped CSV per run to `backtest/reports/` (these CSVs are committed — don't
  assume the directory is disposable).
- **`analytics/`** — performance stats (win rate, expectancy, Sharpe, drawdown) and equity curve,
  computed from `trade_history/trade_history.csv`.
- **`telegram/telegram_bot.py`** — sends trade notifications; failures here should not break the trading
  loop.
- **`docs/feature_manager.py` + `docs/features.json`** — a `show_features()` startup banner describing
  which features are enabled; not related to tests.

### Bot lifecycle (`core/bot.py: TradingBot`)

1. `__init__` builds the data provider + broker via their factories, and checks
   `trade_history/open_positions.csv` for a position left open by a crashed/killed previous run
   (crash recovery) — if found, it's handed to `PositionManager` before anything else runs.
2. `run_continuously()`: waits for market open if started early, resumes monitoring any recovered
   position, then loops `run()` every 5 minutes while `check_market_session()` is true.
3. `run()` per cycle: enforce the entry time window (`TRADE_ENTRY_START_TIME`..`NO_NEW_ENTRY_AFTER`) →
   fetch data → compute indicators → optionally run an inline backtest (`RUN_BACKTEST`) → generate signal
   → skip if a trade is already open (single-position bot) → size/validate risk → place order → **block
   synchronously in `monitor_open_trade()` until that position closes** → show performance/dashboard.
4. `monitor_open_trade()` is a tight polling loop (`TRADE_MONITOR_INTERVAL` seconds) that fetches a real
   live LTP each tick (never falls back to the entry price — a stale/fake price could hide a stop-loss
   breach), then in order: checks the 3:10 PM last-trade force-exit, the time-based max-holding exit, the
   EOD exit, updates break-even/trailing stop, prints status, checks partial-profit booking, then
   target/stop-loss. Force-exit checks must run even when live LTP is temporarily unavailable (falls back
   to last known price) — the loop must never stall on missing data, since it blocks the entire bot's
   outer scan loop while a position is open.

### Signal confluence

`generate_trading_signal()` treats CHOPPY market regime and VWAP/contra-trend direction checks as hard
blocks, but scores `strong_trend` and higher-timeframe confirmation instead of AND-ing every filter
together (`SIGNAL_CONFIRMATIONS_REQUIRED` in settings controls how many of those 2 must pass) — this was
a deliberate relaxation after the original all-AND chain produced zero trades for days. Keep this
distinction in mind before adding new filters: prefer scoring over stacking another hard AND unless the
filter is a genuine directional/safety gate.
