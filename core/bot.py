import time
from datetime import datetime, time as dt_time, timedelta
from zoneinfo import ZoneInfo


# ============================================================
# LOGGER
# ============================================================

from logger.logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

from config.settings import (
    BROKER,
    DATA_PROVIDER,
    PAPER_TRADING,
    TRADE_MONITOR_INTERVAL,
    RUN_BACKTEST,
    PARTIAL_EXIT_ENABLE,
    PARTIAL_EXIT_TRIGGER_RR,
    BREAK_EVEN_TRIGGER_RR,
    SIGNAL_CONFIRMATIONS_REQUIRED,
    NO_NEW_ENTRY_AFTER,
    TRADE_ENTRY_START_TIME,
    LAST_TRADE_FORCE_EXIT_TIME,
    TIME_EXIT_ENABLE,
    MAX_HOLDING_MINUTES,
    LTP_MAX_STALE_SECONDS,
    WHIPSAW_COOLDOWN_ENABLE,
    FAST_STOP_HOLD_MINUTES,
    CONSECUTIVE_FAST_STOPS_TRIGGER,
    WHIPSAW_COOLDOWN_MINUTES,
)


# ============================================================
# MARKET DATA
# ============================================================

from market_data.data_provider_factory import DataProviderFactory
from market_data.market_data import get_nifty_data


# ============================================================
# INDICATORS
# ============================================================

from indicators.indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_volume_average,
    calculate_atr,
    calculate_adx,
    calculate_vwap,
)


# ============================================================
# STRATEGY
# ============================================================
from strategy.vwap_filter import is_vwap_confirmed
from strategy.strategy import generate_signal
from strategy.strike_selector import select_best_strike

from strategy.market_regime import (
    detect_market_regime,
    is_atr_expanding,
)

from strategy.trend_strength import trend_strength

from strategy.mtf_filter import (
    get_higher_timeframe_trend,
    is_higher_timeframe_confirmed,
)

from strategy.trend_filter import get_trend


# ============================================================
# RISK MANAGEMENT
# ============================================================

from risk.position_size import calculate_position_size

from risk.risk_manager import (
    calculate_trade,
    calculate_pnl,
)

from risk.trailing_stop import update_trailing_stop
from risk.break_even import move_to_break_even
from risk.atr_converter import convert_atr_to_option_premium


# ============================================================
# TRADE MANAGEMENT
# ============================================================

from trade.partial_exit import calculate_partial_exit

from trade.trade_state import TradeState
from trade.order_manager import OrderManager
from trade.order_history import save_order_history
from trade.position_manager import PositionManager

# REMOVED: `from trade.position_monitor import PositionMonitor`
# trade/position_monitor.py was deleted (it was dead code - never
# actually used anywhere in run()/monitor_open_trade()). Keeping this
# import would crash the bot on startup with ModuleNotFoundError.


# ============================================================
# BROKER
# ============================================================

from broker.paper_broker import PaperBroker
from broker.broker_factory import BrokerFactory


# ============================================================
# PAPER TRADING
# ============================================================

from paper_trade.trade_validator import validate_trade

from paper_trade.paper_trade import (
    execute_paper_trade,
    save_trade,
    monitor_trade,
    close_paper_trade,
    is_eod_exit_time,
    load_open_trade,
)


# ============================================================
# TRADE HISTORY
# ============================================================

from trade_history.trade_history import save_trade_history


# ============================================================
# PORTFOLIO
# ============================================================

from portfolio.portfolio_manager import portfolio_summary, unlock_capital


# ============================================================
# PNL / TRADE STATUS
# ============================================================

from trade.pnl_engine import get_trade_status


# ============================================================
# PRICING
# ============================================================

from pricing.dynamic_option_price import DynamicOptionPricing


# ============================================================
# EXECUTION (SLIPPAGE / CHARGES)
# ============================================================
# FIX: this cost-model engine existed in the repo but had zero callers
# anywhere -- every reported P&L (console, CSVs, Telegram) was the raw
# premium delta with no brokerage/STT/GST/slippage deducted, making
# paper-trading look more profitable than live trading would actually
# be. Now applied to the partial-exit leg here and to the final-close
# leg in paper_trade.close_paper_trade().

from execution.slippage import apply_slippage
from execution.charges import calculate_charges


# ============================================================
# ANALYTICS
# ============================================================

from analytics.performance import calculate_performance, calculate_daily_summary
from analytics.equity_curve import calculate_equity_curve


# ============================================================
# BACKTEST
# ============================================================

from backtest.backtest import run_backtest
from backtest.report import save_backtest_report


# ============================================================
# REPORTS / DASHBOARD
# ============================================================

from reports.dashboard import show_dashboard


# ============================================================
# TELEGRAM
# ============================================================

from telegram.telegram_bot import send_telegram_message


# ============================================================
# MARKET SESSION
# ============================================================

from utils.market_session import is_market_open


# ============================================================
# FEATURES / DOCUMENTATION
# ============================================================

from docs.feature_manager import show_features

# REMOVED: `from market_simulator.simulator import simulate_price`
# This was a random-walk price generator (random.uniform(-5, 5)) that
# was being used to "monitor" live trades. It's no longer used —
# monitor_open_trade() now fetches real LTP via self.data_provider.
# market_simulator/simulator.py itself is left untouched in case you
# want it for something else later (e.g. quick offline UI testing).


class TradingBot:

    def __init__(self):

        print("=" * 50)
        print("Trading Bot Initialized")
        print("=" * 50)

        # Trade State
        self.trade_state = TradeState()

        # Data Provider
        self.data_provider = DataProviderFactory.create_provider(
            DATA_PROVIDER
        )

        # Broker
        self.broker = BrokerFactory.create_broker(
            BROKER
        )

        print("\n========== SYSTEM CONFIGURATION ==========")

        print(f"Data Provider : {DATA_PROVIDER}")
        print(f"Provider Class: {type(self.data_provider).__name__}")

        print(f"Broker        : {BROKER}")
        print(f"Broker Class  : {type(self.broker).__name__}")

        print(f"Paper Trading : {PAPER_TRADING}")

        print("==========================================")

        # ==========================================
        # WHIPSAW COOLDOWN STATE
        # ==========================================
        # Per-direction so a CALL streak/cooldown never affects PUT and
        # vice versa. See config/settings.py's WHIPSAW_COOLDOWN_* block
        # for the reasoning and the 2026-09-01 data that shaped it.
        self.whipsaw_state = {
            "BUY CALL": {"consecutive_fast_stops": 0, "cooldown_until": None},
            "BUY PUT": {"consecutive_fast_stops": 0, "cooldown_until": None},
        }

        # Managers
        self.order_manager = OrderManager(self.broker)

        self.position_manager = PositionManager(
            self.trade_state
        )

        # NOTE: PositionMonitor removed along with its dead file.
        # All monitoring now happens directly in monitor_open_trade().

        # ==========================================
        # CRASH RECOVERY
        # ==========================================
        # If the bot crashed/was killed while a trade was open,
        # open_positions.csv still has that row (remove_open_trade()
        # never ran). Check for it here and, if found, hand it to
        # PositionManager so run_continuously() resumes monitoring it
        # BEFORE scanning for any new signal.
        self.recovered_trade = load_open_trade()

        if self.recovered_trade:

            logger.warning(
                f"Recovered an open position from a previous session: "
                f"{self.recovered_trade['Signal']} "
                f"{self.recovered_trade['Strike']} "
                f"{self.recovered_trade['OptionType']} @ "
                f"{self.recovered_trade['Entry']}"
            )

            self.position_manager.open_position(self.recovered_trade)

    def run_continuously(self):

        print("\n========== LIVE TRADING STARTED ==========\n")

        try:

            # NEW: If the bot is started before market hours (e.g. run
            # 1 hour early before leaving for the day), wait here
            # instead of exiting immediately. Without this,
            # check_market_session() returning False on the very
            # first loop iteration below would print "Market Closed"
            # and shut the bot down right away.
            self.wait_for_market_open()

            # Resume monitoring any position recovered from a
            # previous crashed/interrupted session BEFORE the normal
            # scan loop starts.
            if self.recovered_trade:

                print(
                    "\n[RECOVERY] Resuming monitoring of a position "
                    "found open from a previous session...\n"
                )

                self.monitor_open_trade(self.recovered_trade)

                self.recovered_trade = None

            while True:

                # =================================
                # MARKET SESSION CHECK
                # =================================

                if not self.check_market_session():

                    print("\nMarket Closed.")
                    print("Trading Bot Stopped for Today.")

                    self.show_market_close_summary()

                    break

                # =================================
                # TRADING CYCLE
                # =================================

                print("\nRunning Trading Cycle...\n")

                try:

                    self.run()

                except Exception as e:

                    # FIX: a single cycle's exception (e.g. a transient
                    # Kite API network/read timeout while fetching market
                    # data) used to be unhandled here, propagating out of
                    # the while loop and killing the entire day's bot
                    # process minutes after market open. Log it and keep
                    # the scan loop alive instead - the next cycle 5
                    # minutes later will simply retry. If a position was
                    # already open in-memory when this cycle failed, the
                    # next self.run() call finds it via position_manager
                    # and resumes monitoring it rather than opening a
                    # second position.

                    logger.error(
                        f"Trading cycle failed with an unhandled "
                        f"exception, will retry next cycle: {e}",
                        exc_info=True
                    )

                    print(
                        f"\n[ERROR] Trading cycle failed: {e}\n"
                        f"Will retry on next scan.\n"
                    )

                # =================================
                # NEXT SCAN
                # =================================

                print("\nNext Scan in 5 Minutes...\n")

                time.sleep(300)

        except KeyboardInterrupt:

            print("\nStopping Trading Bot...")

        finally:

            print("\nTrading Bot Closed Successfully.")

    def fetch_market_data(self):

        logger.info("Downloading Market Data...")

        # ==========================================
        # NIFTY SPOT DATA
        # ==========================================

        data = self.data_provider.get_market_data()

        # ==========================================
        # NIFTY FUTURES DATA FOR VWAP
        # ==========================================

        futures_data = self.data_provider.get_nifty_futures_data()

        # ==========================================
        # CALCULATE FUTURES VWAP
        # ==========================================

        futures_data = calculate_vwap(futures_data)

        # Latest completed/available Futures VWAP
        futures_vwap = futures_data["VWAP"].iloc[-1]

        print("\n========== FUTURES VWAP ==========")
        print(f"Futures VWAP : {round(futures_vwap, 2)}")
        print(
            f"Futures Close: "
            f"{round(futures_data['Close'].iloc[-1], 2)}"
        )
        print("==================================")

        # Store for later signal confirmation
        self.futures_vwap_data = futures_data
        self.futures_vwap = futures_vwap
        return data

    def calculate_indicators(self, data):

        data = calculate_ema(data)
        data = calculate_ema(data, 50)

        data = calculate_rsi(data)
        data = calculate_volume_average(data)
        data = calculate_atr(data)
        data = calculate_adx(data)

        logger.debug(
            f"\n{data[['EMA_20', 'EMA_50', 'RSI', 'ATR', 'ADX']].tail()}"
        )
        logger.debug(f"CANDLE COUNT: {len(data)}")
        logger.debug(f"CLOSE NaN: {data['Close'].isna().sum()}")
        logger.debug(f"HIGH NaN: {data['High'].isna().sum()}")
        logger.debug(f"LOW NaN: {data['Low'].isna().sum()}")

        return data

    def generate_trading_signal(self, data):

        close_price = float(data.iloc[-1]["Close"])

        option = self.data_provider.get_option_chain(close_price)

        # FIX: get_option_chain() catches its own internal exceptions
        # (rate limiting, cookie expiry, schema change) and returns
        # None on failure. Subscripting it unconditionally below used
        # to raise an unhandled TypeError that masked the real error
        # and crashed the trading cycle instead of just skipping it.
        if option is None:
            print("\nOption Chain Unavailable")
            print("Trade Skipped")
            return "NO TRADE", None

        print("\n========== AVAILABLE STRIKES ==========")

        for strike in option["Strikes"]:
            print(
                f"{strike['Strike']} {strike['Type']} | "
                f"LTP: {strike['LTP']} | "
                f"OI: {strike['OI']} | "
                f"Volume: {strike['Volume']}"
            )

        print("=======================================")
        print("\n========== OPTION CHAIN ==========")
        print(f"PCR        : {option['PCR']}")
        print(f"Call OI    : {option['Call_OI']}")
        print(f"Put OI     : {option['Put_OI']}")
        print(f"ATM Strike : {option['ATM_Strike']}")
        print("==================================")

        trend = get_trend(data)
        strong_trend, ema_gap = trend_strength(data)

        # FIX: fetch HTF data from the SAME provider (Kite) as the main 5m
        # data, instead of yfinance, to avoid cross-source price mismatches
        # that were causing false HTF-mismatch skips. Falls back to yfinance
        # only if the active provider doesn't support the interval param
        # (e.g. a non-Kite DataProvider implementation).
        try:
            data_15m = self.data_provider.get_market_data(
                interval="15minute", days=5
            )
        except TypeError:
            data_15m = get_nifty_data(interval="15m")

        higher_trend = get_higher_timeframe_trend(data_15m)
        htf_confirmed = is_higher_timeframe_confirmed(trend, higher_trend)

        adx = float(data.iloc[-1]["ADX"])
        atr_expanding = is_atr_expanding(data)
        market_regime = detect_market_regime(adx, ema_gap, atr_expanding)

        print(f"Trend      : {trend}")
        print(f"HTF Trend  : {higher_trend}")

        print("\n========== MARKET REGIME ==========")
        print(f"ADX            : {round(adx,2)}")
        print(f"Market Regime  : {market_regime}")
        print(f"ATR Expanding  : {atr_expanding}")
        print(f"EMA Gap        : {ema_gap}")
        print(f"Strong Trend   : {strong_trend}")
        print("==================================")

        # ===============================
        # CHOPPY market is always a hard block -- a genuinely flat/
        # directionless market shouldn't be traded regardless of other
        # confirmations passing.
        #
        # FIX (2026-08-31 loss review): TREND EXHAUSTION (very high ADX,
        # non-expanding ATR) is blocked the same way. That trade passed
        # confluence 2/2 (Strong Trend + HTF Confirmed both look only at
        # EMA gap / trend direction, not ADX/ATR) despite the regime
        # engine already flagging the setup as stalled, then whipsawed
        # for the full 45-minute hold and closed at -131.22 on the time
        # exit. See config/settings.py's ADX_EXHAUSTION_THRESHOLD comment.
        # ===============================
        if market_regime in ("CHOPPY", "TREND EXHAUSTION"):

            print(f"\nMarket is {market_regime.title()}")
            print("Trade Skipped")

            return "NO TRADE", None

        # ===============================
        # FIX: strong_trend and HTF-confirmation used to BOTH be hard
        # AND gates (on top of the CHOPPY check, the EMA/RSI/PCR signal,
        # the VWAP confirmation, and the contra-trend block below) --
        # a 5-6 stage AND-chain that was almost impossible to pass
        # together, causing zero trades across multiple sessions.
        #
        # These are now scored: SIGNAL_CONFIRMATIONS_REQUIRED (in
        # config/settings.py) controls how many of the 3 must pass.
        # Default = 2 (was 2 of 2 before atr_expanding was added below
        # on 2026-08-31 -- see settings.py comment for the net effect).
        # Set it to 1 in settings.py if logs show these are what's most
        # often blocking trades, or to 3 for the old strict AND.
        #
        # FIX (2026-08-31 loss review): added atr_expanding as a 3rd
        # scored vote -- a real volatility expansion is itself evidence
        # the move is genuine, so it can now stand in for strong_trend
        # or htf_confirmed when only one of those two holds. This is
        # additive only (anything that passed 2-of-2 before still
        # passes); it does NOT reopen today's ADX=72.45/flat-ATR trade,
        # which is blocked earlier by the TREND EXHAUSTION regime check
        # above regardless of this score.
        # ===============================

        confirmations_passed = sum([strong_trend, htf_confirmed, atr_expanding])

        print("\n========== CONFLUENCE CHECK ==========")
        print(f"Strong Trend    : {strong_trend}")
        print(f"HTF Confirmed   : {htf_confirmed}")
        print(f"ATR Expanding   : {atr_expanding}")
        print(f"Passed          : {confirmations_passed} / 3")
        print(f"Required        : {SIGNAL_CONFIRMATIONS_REQUIRED}")
        print("=======================================")

        if confirmations_passed < SIGNAL_CONFIRMATIONS_REQUIRED:

            print("\nInsufficient Confluence")
            print("Trade Skipped")

            return "NO TRADE", None

        signal = generate_signal(
            data,
            option,
            debug=True,
        )

        # NEW: explicit, grep-able marker for the CORE signal (from
        # EMA/RSI/PCR alone) BEFORE VWAP confirmation or the
        # contra-trend filter can override it below. Needed to trace,
        # at end of day, how many BUY CALL/BUY PUT signals were
        # generated in the first place vs how many were subsequently
        # blocked (missed) by a downstream filter.
        print(f"\nCore Signal (pre-filters) : {signal}")

        # ===============================
        # VWAP CONFIRMATION
        # ===============================

        futures_close = float(
            self.futures_vwap_data["Close"].iloc[-1]
        )

        futures_vwap = float(
            self.futures_vwap_data["VWAP"].iloc[-1]
        )

        print("\n========== VWAP FILTER ==========")
        print(f"Futures Close : {round(futures_close, 2)}")
        print(f"Futures VWAP  : {round(futures_vwap, 2)}")

        if futures_close > futures_vwap:
            print("VWAP Bias     : BULLISH")
        elif futures_close < futures_vwap:
            print("VWAP Bias     : BEARISH")
        else:
            print("VWAP Bias     : NEUTRAL")

        print("=================================")

        if signal in ("BUY CALL", "BUY PUT"):

            if not is_vwap_confirmed(
                signal,
                futures_close,
                futures_vwap
            ):

                print("\nVWAP Confirmation Failed")
                print("Trade Skipped")

                return "NO TRADE", None

        # ===============================
        # Trend Filter (directional hard block -- keep as-is)
        # ===============================

        if trend == "UPTREND" and signal == "BUY PUT":
            print("Trend Filter : BUY PUT blocked (Uptrend)")
            signal = "NO TRADE"

        elif trend == "DOWNTREND" and signal == "BUY CALL":
            print("Trend Filter : BUY CALL blocked (Downtrend)")
            signal = "NO TRADE"

        print(f"Final Signal : {signal}")

        selected_strike = select_best_strike(signal, option)

        print("\n========== SELECTED STRIKE ==========")

        if selected_strike:
            print(f"Strike : {selected_strike['Strike']}")
            print(f"Type   : {selected_strike['Type']}")
            print(f"LTP    : {selected_strike['LTP']}")
            print(f"OI     : {selected_strike['OI']}")
            print(f"Volume : {selected_strike['Volume']}")
        else:
            print("No Strike Selected")

        print("=====================================")

        logger.info(f"Trading Signal : {signal}")

        return signal, selected_strike

    def manage_risk(self, signal, data, selected_strike):

        entry_price = DynamicOptionPricing.get_entry_price(selected_strike)

        if entry_price is None:
            return None, None, None

        index_atr = float(data.iloc[-1]["ATR"])

        option_atr = convert_atr_to_option_premium(index_atr)

        print("\n===== ATR CONVERSION =====")
        print(f"Entry Price : {entry_price}")
        print(f"Index ATR   : {index_atr}")
        print(f"Option ATR  : {option_atr}")
        print("==========================")

        trade = calculate_trade(
            entry_price,
            option_atr,
        )

        trade["Strike"] = selected_strike["Strike"]
        trade["OptionType"] = selected_strike["Type"]

        trade["Risk"] = trade["ATR"] * trade["ATRMultiplier"]

        position = calculate_position_size(
            trade["Entry"],
            trade["StopLoss"]
        )

        trade["Quantity"] = position["Quantity"]

        validation = validate_trade(position)

        return trade, position, validation

    def execute_trade_flow(self, signal, trade, selected_strike):

        # Place Order
        paper_trade = self.order_manager.place_order(signal, trade)

        if paper_trade is None:
            print("\nOrder Placement Failed.")
            return None

        paper_trade["Quantity"] = trade["Quantity"]
        paper_trade["OriginalQuantity"] = trade["Quantity"]
        paper_trade["PartialBooked"] = False

        # Save Order History
        save_order_history(paper_trade)

        # Add Trade Details
        paper_trade["Strike"] = selected_strike["Strike"]
        paper_trade["OptionType"] = selected_strike["Type"]

        # FIX: store the exact tradingsymbol so monitor_open_trade() can
        # fetch a real live LTP for THIS contract while the trade is
        # open, instead of relying on the old random-walk simulator.
        paper_trade["Symbol"] = selected_strike.get("Symbol", "")

        paper_trade["ATR"] = trade.get("ATR", 0)
        paper_trade["ATRMultiplier"] = trade.get("ATRMultiplier", 0)
        paper_trade["RiskReward"] = trade.get("RiskReward", 0)
        paper_trade["Risk"] = trade.get("Risk", 0)
        paper_trade["OrderID"] = paper_trade.get("OrderID", "")
        entry_now = datetime.now(ZoneInfo("Asia/Kolkata"))
        paper_trade["EntryTime"] = entry_now.isoformat()
        paper_trade["IsLastWindowTrade"] = (
            entry_now.hour == 14 and entry_now.minute == 45
        )
        paper_trade["EventTimeline"] = [
            {
                "Time": entry_now.isoformat(),
                "Event": "TRADE EXECUTED",
                "Price": paper_trade.get("Entry"),
            }
        ]
        # Backward-compatible fields for existing storage/history code.
        paper_trade["Timestamp"] = entry_now.strftime("%Y-%m-%d %H:%M:%S")
        paper_trade["Time"] = paper_trade.get("Time", paper_trade["Timestamp"])
        paper_trade["LastKnownPrice"] = paper_trade.get("Entry")
        paper_trade["LastLTPTime"] = entry_now.isoformat()
        paper_trade["PnL"] = ""

        # Open Position
        self.position_manager.open_position(paper_trade)

        # Show Active Position
        self.position_manager.print_position()

        # Save Trade
        save_trade(paper_trade)

        # Telegram Notification
        message = f"""
    📢 OPTION BUYING BOT

    Signal : {signal}

    Entry : {paper_trade['Entry']}
    Stop Loss : {paper_trade['StopLoss']}
    Target : {paper_trade['Target']}

    Status : {paper_trade['Status']}
    """

        self.send_notification(message)

        # Print Trade
        self.print_paper_trade(paper_trade)

        return paper_trade

    def get_live_premium(self, trade):
        """Fetch live LTP and cache the last valid price.

        Important: never fall back to Entry price. Entry can be far away from
        the real market and can hide a stop-loss breach during a data outage.
        Returns None when no fresh/recent reliable price is available.
        """
        symbol = trade.get("Symbol")
        now = datetime.now(ZoneInfo("Asia/Kolkata"))

        if not symbol:
            logger.error("Trade has no Symbol; cannot safely monitor LTP.")
            return None

        try:
            price = self.data_provider.get_ltp(symbol)
            if price is None or float(price) <= 0:
                raise ValueError(f"Invalid LTP: {price}")

            price = float(price)
            trade["LastKnownPrice"] = price
            trade["LastLTPTime"] = now.isoformat()
            return price

        except Exception as e:
            logger.error(f"LTP fetch failed for {symbol}: {e}")

            cached_price = trade.get("LastKnownPrice")
            cached_time = trade.get("LastLTPTime")
            if cached_price is not None and cached_time:
                try:
                    age = (now - datetime.fromisoformat(cached_time)).total_seconds()
                    if age <= LTP_MAX_STALE_SECONDS:
                        logger.warning(
                            f"Using cached LTP {cached_price} for {symbol}; "
                            f"age={age:.1f}s"
                        )
                        return float(cached_price)
                except Exception:
                    pass

            logger.error("No safe fresh/recent LTP available; skipping price decision.")
            return None

    def _entry_time_from_trade(self, trade):
        """Return timezone-aware entry time for new and old trade records."""
        ist = ZoneInfo("Asia/Kolkata")
        value = trade.get("EntryTime") or trade.get("Timestamp") or trade.get("Time")
        if not value:
            raise ValueError("Open trade has no entry timestamp")

        try:
            entry_time = datetime.fromisoformat(str(value))
        except ValueError:
            entry_time = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")

        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=ist)
        else:
            entry_time = entry_time.astimezone(ist)
        return entry_time

    def _now_ist(self):
        return datetime.now(ZoneInfo("Asia/Kolkata"))

    def _event_time(self):
        return self._now_ist().strftime("%Y-%m-%d %H:%M:%S IST")

    def _add_trade_event(self, trade, event, **details):
        record = {"Time": self._now_ist().isoformat(), "Event": event}
        record.update(details)
        trade.setdefault("EventTimeline", []).append(record)

    def _print_trade_timeline(self, trade):
        print("\n========== TRADE TIMELINE ==========")
        for event in trade.get("EventTimeline", []):
            try:
                event_time = datetime.fromisoformat(event["Time"]).astimezone(
                    ZoneInfo("Asia/Kolkata")
                ).strftime("%H:%M:%S IST")
            except Exception:
                event_time = str(event.get("Time", ""))
            print(f"{event_time} | {event.get('Event', '')}")
        print("====================================")

    def _print_exit_summary(
        self,
        trade,
        close_result,
        reason,
        entry_time,
        exit_time,
        elapsed_minutes,
        peak_price,
    ):
        """
        NEW METHOD — unified exit summary, printed for EVERY exit path
        (Target Hit, Stop Loss Hit, Time Exit, EOD Exit, Last-Trade-
        Window Exit) so the console always shows the same complete
        picture: signal/strike, entry premium, exit premium, the
        Stop Loss level, Target, WHY it exited, entry/exit time,
        how long it was held, the highest premium seen during the
        hold, and the final P&L.
        """

        print("\n========== TRADE CLOSED ==========")
        print(f"Reason          : {reason}")
        print(f"Signal          : {trade.get('Signal', '')}")
        print(
            f"Strike          : {trade.get('Strike', '')} "
            f"{trade.get('OptionType', '')}"
        )
        print(f"Entry Premium   : {trade['Entry']}")

        if close_result:
            print(f"Exit Premium    : {close_result['ExitPrice']}")
        else:
            print("Exit Premium    : (close failed - see error above)")

        print(f"Stop Loss Level : {trade['StopLoss']}")
        print(f"Target Level    : {trade['Target']}")
        print(f"Peak Premium    : {peak_price} (highest LTP seen during hold)")
        print(f"Entry Time      : {entry_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
        print(f"Exit Time       : {exit_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
        print(f"Holding Time    : {int(elapsed_minutes)} min")

        if close_result:
            print(f"Partial P&L     : {close_result.get('PartialPnL', 0)}")
            print(f"Final P&L       : {close_result.get('FinalPnL', 0)}")
            print(f"Total P&L       : {close_result['PnL']}")
            print(f"Return          : {close_result['PnLPercent']} %")

        print("===================================")

    def _update_whipsaw_state(self, trade, exit_reason, pnl, elapsed_minutes):
        """
        Called from every exit path in monitor_open_trade(). Tracks, per
        direction (CALL/PUT independently), how many FAST stop-losses
        (a LOSING trade closed via STOP LOSS HIT within
        FAST_STOP_HOLD_MINUTES) have happened in a row. Any other
        outcome for that direction -- a win, a slower stop-loss, a
        time/EOD/last-trade exit -- resets its streak to zero.

        Once CONSECUTIVE_FAST_STOPS_TRIGGER is reached, that direction
        gets a WHIPSAW_COOLDOWN_MINUTES cooldown (checked by
        _is_whipsaw_cooldown_active() before any new entry in run()).
        """

        if not WHIPSAW_COOLDOWN_ENABLE:
            return

        signal = trade.get("Signal")

        if signal not in self.whipsaw_state:
            return

        state = self.whipsaw_state[signal]

        is_fast_loss = (
            exit_reason == "STOP LOSS HIT"
            and elapsed_minutes <= FAST_STOP_HOLD_MINUTES
            and pnl < 0
        )

        if is_fast_loss:

            state["consecutive_fast_stops"] += 1

            print(
                f"[WHIPSAW TRACK] {signal}: fast stop-loss "
                f"#{state['consecutive_fast_stops']} in a row "
                f"(held {elapsed_minutes:.1f} min, PnL {pnl})."
            )

            if state["consecutive_fast_stops"] >= CONSECUTIVE_FAST_STOPS_TRIGGER:

                cooldown_until = self._now_ist() + timedelta(
                    minutes=WHIPSAW_COOLDOWN_MINUTES
                )
                state["cooldown_until"] = cooldown_until

                print(
                    f"[WHIPSAW COOLDOWN ACTIVATED] {signal} entries "
                    f"blocked until {cooldown_until.strftime('%H:%M:%S')} "
                    f"IST ({WHIPSAW_COOLDOWN_MINUTES} min) after "
                    f"{state['consecutive_fast_stops']} consecutive fast "
                    f"stop-losses."
                )

        else:

            if state["consecutive_fast_stops"] > 0:
                print(
                    f"[WHIPSAW TRACK] {signal}: streak reset "
                    f"(this exit wasn't a fast stop-loss)."
                )

            state["consecutive_fast_stops"] = 0
            state["cooldown_until"] = None

    def _is_whipsaw_cooldown_active(self, signal):
        """
        Returns True (and blocks) if `signal`'s direction is currently
        cooling down after CONSECUTIVE_FAST_STOPS_TRIGGER fast
        stop-losses in a row. Naturally clears (and resets that
        direction's streak to zero, a clean slate) once the cooldown
        window has elapsed.
        """

        if not WHIPSAW_COOLDOWN_ENABLE or signal not in self.whipsaw_state:
            return False

        state = self.whipsaw_state[signal]
        cooldown_until = state.get("cooldown_until")

        if cooldown_until is None:
            return False

        now = self._now_ist()

        if now < cooldown_until:

            remaining = (cooldown_until - now).total_seconds() / 60

            print(
                f"\n[WHIPSAW COOLDOWN ACTIVE] {signal} blocked - "
                f"{state['consecutive_fast_stops']} consecutive fast "
                f"stop-losses. {remaining:.1f} min remaining (until "
                f"{cooldown_until.strftime('%H:%M:%S')} IST)."
            )

            return True

        # Cooldown window has passed -- give this direction a fresh start.
        state["cooldown_until"] = None
        state["consecutive_fast_stops"] = 0

        return False

    def monitor_open_trade(self, trade):
        """
        Monitor an open paper trade using REAL live option premium
        (Kite LTP), with trailing stop, break-even protection and
        partial profit booking. Runs continuously until the position
        is closed (target hit, stop-loss hit, or EOD force-exit).

        FIX (previously, two separate bugs):

          1) current_price was generated by
             market_simulator.simulate_price() -- a random walk, NOT
             real market data. Every open-trade decision (target/SL
             hit, trailing stop, partial exit) was being made on fake
             numbers regardless of what the real option premium was
             actually doing.

          2) The loop only ran for a fixed `range(5)` iterations. If
             the trade hadn't hit target/SL/EOD within those 5 ticks,
             monitoring silently stopped -- but trade_state still
             showed the position as OPEN. Since run() skips scanning
             for new signals whenever a position is already open, the
             bot would get permanently stuck: no further price checks,
             no new trades -- until the process was manually restarted.

        Now: loop runs `while self.position_manager.has_position()`,
        and current_price comes from a real LTP fetch each tick via
        get_live_premium().
        """

        realized_pnl = 0.0
        entry_time = self._entry_time_from_trade(trade)

        # NEW: track the highest premium actually seen while the
        # trade was open. Printed in every exit summary so you can
        # see how much of a favorable move was given back by the
        # time the trade actually closed (e.g. via Time-Exit or
        # trailing stop), even though it's not possible to force an
        # exit to land exactly ON that peak in real time -- by
        # definition you only know a price was the peak once it has
        # already passed (see chat explanation).
        peak_price = trade["Entry"]

        print("\n========== LIVE TRADE MONITOR ==========")
        print(f"Entry Time      : {entry_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
        print(f"Entry Price     : {trade['Entry']}")
        print(f"Initial SL      : {trade['StopLoss']}")
        print(f"Target          : {trade['Target']}")
        if trade.get("IsLastWindowTrade"):
            print(f"Last Trade Rule : FORCE EXIT AT {LAST_TRADE_FORCE_EXIT_TIME} IST")
        print("========================================")

        while self.position_manager.has_position():

            now = datetime.now(ZoneInfo("Asia/Kolkata"))
            elapsed_minutes = max(0.0, (now - entry_time).total_seconds() / 60.0)
            current_price = self.get_live_premium(trade)

            if current_price is not None and current_price > peak_price:
                peak_price = current_price

            # ==========================================
            # FIX: force-exit conditions (Last-Trade-Window,
            # Time-based, EOD) must be checked EVEN WHEN live LTP is
            # temporarily unavailable (e.g. after market hours, a
            # brief API hiccup, or an expired/stale instrument).
            #
            # Previously, current_price == None caused an immediate
            # `continue` BEFORE any of these three checks ran. Since
            # Kite legitimately can't return a fresh LTP outside
            # market hours, a trade left open past market close (or
            # hit by any persistent LTP outage) would loop on
            # `continue` forever -- none of Time-Exit, EOD-Exit, or
            # Last-Trade-Exit could ever fire. Because this loop
            # blocks run_continuously()'s outer scan loop until the
            # position closes, a single stuck trade froze the ENTIRE
            # bot indefinitely: it wouldn't self-exit, and — if this
            # happened one day — it would still be stuck on that same
            # trade the next day too, scanning nothing.
            #
            # Force-exits now use current_price when available, else
            # fall back to the last known real price (or Entry if
            # none yet) so a closing decision can still be made.
            # ==========================================

            exit_reference_price = (
                current_price
                if current_price is not None
                else trade.get("LastKnownPrice", trade["Entry"])
            )

            # ==========================================
            # LAST TRADE FORCE EXIT — 3:10 PM IST
            # ==========================================
            force_hour, force_minute = map(
                int, LAST_TRADE_FORCE_EXIT_TIME.split(":")
            )
            if (
                trade.get("IsLastWindowTrade", False)
                and now.time() >= dt_time(force_hour, force_minute)
            ):
                print(
                    f"\n[{self._event_time()}] "
                    f"LAST TRADE FORCE EXIT @ {exit_reference_price:.2f}"
                )
                close_result = close_paper_trade(
                    trade=trade,
                    exit_price=exit_reference_price,
                    exit_reason="LAST TRADE FORCE EXIT",
                    realized_pnl=realized_pnl,
                )

                # FIX: close_position() used to be called unconditionally
                # here even when close_paper_trade() failed (returned
                # None) -- silently marking a still-open trade as closed
                # in memory while open_positions.csv still had it open
                # and its capital was never unlocked. Now a failed close
                # is logged and retried next tick instead of being
                # dropped on the floor.
                if close_result is None:
                    logger.critical(
                        "[CLOSE FAILED] LAST TRADE FORCE EXIT could not "
                        "close the trade — position remains OPEN and "
                        "will be retried next tick."
                    )
                    print(
                        f"[{self._event_time()}] CLOSE FAILED — "
                        "will retry closing this trade."
                    )
                    time.sleep(TRADE_MONITOR_INTERVAL)
                    continue

                self._add_trade_event(
                    trade, "LAST TRADE FORCE EXIT", Price=exit_reference_price
                )
                self._update_whipsaw_state(
                    trade, "LAST TRADE FORCE EXIT",
                    close_result["PnL"], elapsed_minutes,
                )
                save_trade_history({
                    "Time": trade.get("EntryTime", trade.get("Timestamp", "")),
                    "Signal": trade["Signal"],
                    "Entry": trade["Entry"],
                    "Exit": close_result["ExitPrice"],
                    "StopLoss": trade["StopLoss"],
                    "Target": trade["Target"],
                    "Status": "CLOSED",
                    "ExitReason": "LAST TRADE FORCE EXIT",
                    "PnL": close_result["PnL"],
                    "PnLPercent": close_result["PnLPercent"],
                })
                self.position_manager.close_position()
                self._print_exit_summary(
                    trade, close_result, "LAST TRADE FORCE EXIT",
                    entry_time, now, elapsed_minutes, peak_price,
                )
                self._print_trade_timeline(trade)
                return

            # ==========================================
            # TIME-BASED FORCE EXIT
            # ==========================================
            if TIME_EXIT_ENABLE and elapsed_minutes >= MAX_HOLDING_MINUTES:

                close_result = close_paper_trade(
                    trade=trade,
                    exit_price=exit_reference_price,
                    exit_reason="TIME EXIT",
                    realized_pnl=realized_pnl,
                )

                # FIX: see LAST TRADE FORCE EXIT above -- don't mark the
                # position closed if close_paper_trade() actually failed.
                if close_result is None:
                    logger.critical(
                        "[CLOSE FAILED] TIME EXIT could not close the "
                        "trade — position remains OPEN and will be "
                        "retried next tick."
                    )
                    print(
                        f"[{self._event_time()}] CLOSE FAILED — "
                        "will retry closing this trade."
                    )
                    time.sleep(TRADE_MONITOR_INTERVAL)
                    continue

                save_trade_history({
                    "Time": trade.get("EntryTime", trade.get("Timestamp", trade.get("Time", ""))),
                    "Signal": trade["Signal"],
                    "Entry": trade["Entry"],
                    "Exit": close_result["ExitPrice"],
                    "StopLoss": trade["StopLoss"],
                    "Target": trade["Target"],
                    "Status": "CLOSED",
                    "ExitReason": "TIME EXIT",
                    "PnL": close_result["PnL"],
                    "PnLPercent": close_result["PnLPercent"],
                })

                self.position_manager.close_position()
                self._add_trade_event(trade, "TIME EXIT", Price=exit_reference_price)
                self._update_whipsaw_state(
                    trade, "TIME EXIT", close_result["PnL"], elapsed_minutes
                )
                self._print_exit_summary(
                    trade, close_result, "TIME EXIT",
                    entry_time, now, elapsed_minutes, peak_price,
                )
                self._print_trade_timeline(trade)
                return

            # ==========================================
            # EOD FORCE EXIT
            # ==========================================

            if is_eod_exit_time():

                close_result = close_paper_trade(
                    trade=trade,
                    exit_price=exit_reference_price,
                    exit_reason="EOD EXIT",
                    realized_pnl=realized_pnl,
                )

                # FIX: see LAST TRADE FORCE EXIT above -- don't mark the
                # position closed if close_paper_trade() actually failed.
                if close_result is None:
                    logger.critical(
                        "[CLOSE FAILED] EOD EXIT could not close the "
                        "trade — position remains OPEN and will be "
                        "retried next tick."
                    )
                    print(
                        f"[{self._event_time()}] CLOSE FAILED — "
                        "will retry closing this trade."
                    )
                    time.sleep(TRADE_MONITOR_INTERVAL)
                    continue

                save_trade_history({
                    "Time": trade.get("EntryTime", trade.get("Timestamp", trade.get("Time", ""))),
                    "Signal": trade["Signal"],
                    "Entry": trade["Entry"],
                    "Exit": close_result["ExitPrice"],
                    "StopLoss": trade["StopLoss"],
                    "Target": trade["Target"],
                    "Status": "CLOSED",
                    "PnL": close_result["PnL"],
                    "PnLPercent": close_result["PnLPercent"],
                })

                self.position_manager.close_position()

                self._add_trade_event(trade, "EOD EXIT", Price=exit_reference_price)
                self._update_whipsaw_state(
                    trade, "EOD EXIT", close_result["PnL"], elapsed_minutes
                )
                self._print_exit_summary(
                    trade, close_result, "EOD EXIT",
                    entry_time, now, elapsed_minutes, peak_price,
                )
                self._print_trade_timeline(trade)

                return

            # ==========================================
            # LIVE PRICE UNAVAILABLE — nothing further to evaluate
            # this tick (break-even/trailing/target/SL all need a
            # fresh real price; force-exits above already handled
            # the case where we must close anyway).
            # ==========================================
            if current_price is None:
                print("Live LTP unavailable - no SL/target decision this tick.")
                print(f"Holding Time : {elapsed_minutes:.2f} min")
                time.sleep(TRADE_MONITOR_INTERVAL)
                continue

            # ==========================================
            # BREAK EVEN PROTECTION
            # ==========================================

            old_sl = trade["StopLoss"]
            risk = trade["Risk"]

            # FIX: risk/break_even.py now correctly treats `risk` as an
            # ABSOLUTE value and `trigger_rr` (from config) as the
            # number of R-multiples of profit needed before moving SL
            # to entry. Previously the 4th argument was misread as a
            # raw percentage, causing break-even to fire far too early.
            trade["StopLoss"] = move_to_break_even(
                trade["Entry"],
                current_price,
                trade["StopLoss"],
                risk,
                trigger_rr=BREAK_EVEN_TRIGGER_RR,
            )

            # ==========================================
            # ATR TRAILING STOP LOSS
            # ==========================================

            trade["StopLoss"] = update_trailing_stop(
                current_price,
                trade["StopLoss"],
                trade["ATR"],
                trade["ATRMultiplier"]
            )

            if trade["StopLoss"] != old_sl:
                self._add_trade_event(
                    trade, "STOP LOSS UPDATED", OldSL=old_sl,
                    NewSL=trade["StopLoss"]
                )
                print(
                    f"[{self._event_time()}] SL UPDATED | "
                    f"{old_sl} -> {trade['StopLoss']}"
                )
                logger.debug(
                    f"Break Even / Trailing SL Updated: "
                    f"{old_sl} -> {trade['StopLoss']}"
                )

            # ==========================================
            # DISPLAY TRADE STATUS
            # ==========================================

            live_pnl = (current_price - trade["Entry"]) * trade["Quantity"]
            print(
                f"[{now.strftime('%H:%M:%S IST')}] "
                f"LTP={current_price:.2f} | "
                f"PnL={live_pnl + realized_pnl:.2f} | "
                f"SL={trade['StopLoss']:.2f} | "
                f"TARGET={trade['Target']:.2f} | "
                f"HOLD={int(elapsed_minutes)}m"
            )

            # ==========================================
            # PARTIAL PROFIT BOOKING
            # ==========================================

            # NEW: trigger partial booking once profit reaches
            # PARTIAL_EXIT_TRIGGER_RR x the trade's own initial risk,
            # instead of waiting for the full Target. The full Target
            # was often not reached before a reversal gave back the
            # entire unrealized profit via the trailing stop.
            partial_exit_price = (
                trade["Entry"] + (trade["Risk"] * PARTIAL_EXIT_TRIGGER_RR)
            )

            if (
                PARTIAL_EXIT_ENABLE
                and current_price >= partial_exit_price
                and trade.get("PartialBooked", False) is False
            ):

                exit_qty, remaining_qty = calculate_partial_exit(
                    trade["Quantity"]
                )

                # FIX: unlock the capital that was locked (at entry
                # price) for the slice of the position being exited
                # here. Previously only the FINAL remaining quantity's
                # capital was ever unlocked (in close_paper_trade()),
                # so every partial exit permanently shrank available
                # balance even though this much capital was no longer
                # at risk -- eventually causing valid new trades to be
                # rejected with "Insufficient Balance".
                unlock_capital(trade["Entry"] * exit_qty)

                actual_exit_price = apply_slippage(current_price, "SELL")
                charges = calculate_charges(
                    trade["Entry"], actual_exit_price, exit_qty
                )

                partial_pnl = round(
                    (actual_exit_price - trade["Entry"]) * exit_qty
                    - charges["TotalCharges"],
                    2
                )

                realized_pnl += partial_pnl
                self._add_trade_event(
                    trade, "PARTIAL PROFIT BOOKED", Price=current_price
                )
                print(f"[{self._event_time()}] PARTIAL PROFIT BOOKED")

                print("\n=================================")
                print("      PARTIAL PROFIT BOOKING")
                print("=================================")

                print(f"Entry Price        : {trade['Entry']}")
                print(f"Partial Exit Price : {current_price} (fill: {actual_exit_price})")
                print(f"Exit Quantity      : {exit_qty}")
                print(f"Remaining Quantity : {remaining_qty}")
                print(f"Charges            : {charges['TotalCharges']}")
                print(f"Partial P&L        : {partial_pnl}")
                print(f"Realized P&L       : {realized_pnl}")

                trade["Quantity"] = remaining_qty
                trade["StopLoss"] = trade["Entry"]
                trade["PartialBooked"] = True

                print("\nPartial Profit Booked Successfully!")

            # ==========================================
            # CHECK TARGET / STOP LOSS
            # ==========================================

            trade_status = monitor_trade(
                current_price,
                trade
            )

            if trade_status == "TARGET HIT":

                close_result = close_paper_trade(
                    trade=trade,
                    exit_price=current_price,
                    exit_reason="TARGET HIT",
                    realized_pnl=realized_pnl,
                )

                # FIX: see LAST TRADE FORCE EXIT above -- don't mark the
                # position closed if close_paper_trade() actually failed.
                if close_result is None:
                    logger.critical(
                        "[CLOSE FAILED] TARGET HIT could not close the "
                        "trade — position remains OPEN and will be "
                        "retried next tick."
                    )
                    print(
                        f"[{self._event_time()}] CLOSE FAILED — "
                        "will retry closing this trade."
                    )
                    time.sleep(TRADE_MONITOR_INTERVAL)
                    continue

                self._add_trade_event(trade, "TARGET HIT", Price=current_price)
                self._update_whipsaw_state(
                    trade, "TARGET HIT", close_result["PnL"], elapsed_minutes
                )
                save_trade_history({
                    "Time": trade.get("EntryTime", trade.get("Timestamp", trade.get("Time", ""))),
                    "Signal": trade["Signal"],
                    "Entry": trade["Entry"],
                    "Exit": close_result["ExitPrice"],
                    "StopLoss": trade["StopLoss"],
                    "Target": trade["Target"],
                    "Status": "CLOSED",
                    "PnL": close_result["PnL"],
                    "PnLPercent": close_result["PnLPercent"],
                })

                self.position_manager.close_position()

                self._print_exit_summary(
                    trade, close_result, "TARGET HIT",
                    entry_time, now, elapsed_minutes, peak_price,
                )
                self._print_trade_timeline(trade)

                return

            if trade_status == "STOP LOSS HIT":

                close_result = close_paper_trade(
                    trade=trade,
                    exit_price=current_price,
                    exit_reason="STOP LOSS HIT",
                    realized_pnl=realized_pnl,
                )

                # FIX: see LAST TRADE FORCE EXIT above -- don't mark the
                # position closed if close_paper_trade() actually failed.
                if close_result is None:
                    logger.critical(
                        "[CLOSE FAILED] STOP LOSS HIT could not close "
                        "the trade — position remains OPEN and will be "
                        "retried next tick."
                    )
                    print(
                        f"[{self._event_time()}] CLOSE FAILED — "
                        "will retry closing this trade."
                    )
                    time.sleep(TRADE_MONITOR_INTERVAL)
                    continue

                self._add_trade_event(trade, "STOP LOSS HIT", Price=current_price)
                self._update_whipsaw_state(
                    trade, "STOP LOSS HIT", close_result["PnL"], elapsed_minutes
                )
                save_trade_history({
                    "Time": trade.get("EntryTime", trade.get("Timestamp", trade.get("Time", ""))),
                    "Signal": trade["Signal"],
                    "Entry": trade["Entry"],
                    "Exit": close_result["ExitPrice"],
                    "StopLoss": trade["StopLoss"],
                    "Target": trade["Target"],
                    "Status": "CLOSED",
                    "PnL": close_result["PnL"],
                    "PnLPercent": close_result["PnLPercent"],
                })

                self.position_manager.close_position()

                self._print_exit_summary(
                    trade, close_result, "STOP LOSS HIT",
                    entry_time, now, elapsed_minutes, peak_price,
                )
                self._print_trade_timeline(trade)

                return

            # ==========================================
            # TRADE STILL OPEN
            # ==========================================
            # NOTE: status for this tick is already printed above (the
            # single "[HH:MM:SS IST] LTP=... | PnL=... | SL=... |
            # TARGET=... | HOLD=...m" line) — removed the old
            # redundant multi-line "Trade Status : OPEN" + dict print
            # that used to follow it, so each tick is exactly one line.

            time.sleep(TRADE_MONITOR_INTERVAL)

        print("\n========== TRADE MONITOR END ==========")

    def send_notification(self, message):

        send_telegram_message(message)

    def wait_for_market_open(self):
        """
        NEW METHOD.

        If the bot is started before market hours (e.g. run 1 hour
        early before leaving for the day), this polls every 60
        seconds until the market actually opens (9:15 AM IST),
        instead of check_market_session() immediately returning False
        and shutting the whole bot down.

        Does nothing (returns immediately) if:
          - BYPASS_MARKET_SESSION is True (testing mode)
          - the market is already open
          - today is a weekend (prints a message and returns, rather
            than waiting forever for a market that won't open)
        """

        from config.settings import BYPASS_MARKET_SESSION

        if BYPASS_MARKET_SESSION:
            return

        ist = ZoneInfo("Asia/Kolkata")
        now = datetime.now(ist)

        if now.weekday() >= 5:
            print("\nToday is a weekend. Market will not open.")
            return

        if is_market_open():
            return

        print("\n========== WAITING FOR MARKET OPEN ==========")
        print(f"Bot started early ({now.strftime('%H:%M:%S')} IST).")
        print("Will begin scanning automatically once the market")
        print("opens (9:15 AM IST). Safe to leave this running.")
        print("===============================================\n")

        # FIX: is_market_open() itself prints "Market Closed (Outside
        # Trading Hours)" every time it's called — so it's called
        # exactly ONCE per 60s check here (its own print serves as the
        # status line). Calling it twice per iteration (once for the
        # while-condition, once again inside) was printing the same
        # message twice each cycle.
        while True:

            now = datetime.now(ist)

            if now.weekday() >= 5:
                print("\nToday turned out to be a weekend. Stopping wait.")
                return

            if is_market_open():
                break

            time.sleep(60)

        print("\n[MARKET OPEN] Starting trading cycles...\n")

    def check_market_session(self):

        from config.settings import BYPASS_MARKET_SESSION

        if BYPASS_MARKET_SESSION:

            print("\nMarket Session Bypass Enabled.")
            print("Testing Mode: Market hours ignored.")

            return True

        if is_market_open():

            return True

        print("\nMarket is Closed.")

        return False

    def print_trade_details(self, trade):

        print("\n========== TRADE DETAILS ==========")
        print(f"Entry Price : {trade['Entry']}")
        print(f"ATR         : {trade['ATR']}")
        print(f"ATR Mult.   : {trade['ATRMultiplier']}")
        print(f"RiskReward  : 1:{trade['RiskReward']}")
        print(f"Stop Loss   : {trade['StopLoss']}")
        print(f"Target      : {trade['Target']}")
        print("===================================")

    def print_position_size(self, position):

        print("\n========== POSITION SIZE ==========")
        print(f"Capital      : {position['Capital']}")
        print(f"Risk %       : {position['RiskPercent']}%")
        print(f"Max Loss     : {position['MaxLoss']}")
        print(f"Risk / Lot   : {position['RiskPerLot']}")
        print(f"Lots to Buy  : {position['Lots']}")
        print(f"Quantity     : {position['Quantity']}")
        print(f"Enough Cap.  : {position['EnoughCapital']}")
        print(f"Required Cap.: {position['RequiredCapital']}")
        print("===================================")

    def print_validation(self, validation):

        print("\n========== TRADE VALIDATION ==========")
        print(f"Allowed : {validation['Allowed']}")
        print(f"Reason  : {validation['Reason']}")
        print("======================================")

    def print_portfolio(self, portfolio):

        print("\n========== PORTFOLIO ==========")
        print(f"Initial Capital : {portfolio['InitialCapital']}")
        print(f"Current Balance : {portfolio['CurrentBalance']}")
        print(f"Net Profit      : {portfolio['Profit']}")
        print(f"Return %        : {portfolio['ReturnPercent']}")
        print("================================")

    def print_paper_trade(self, paper_trade):

        print("\n========== PAPER TRADE ==========")
        print(f"Time        : {paper_trade['Time']}")
        print(f"Signal      : {paper_trade['Signal']}")
        print(f"Entry       : {paper_trade['Entry']}")
        print(f"Stop Loss   : {paper_trade['StopLoss']}")
        print(f"Target      : {paper_trade['Target']}")
        print(f"Status      : {paper_trade['Status']}")
        print("=================================")

    def handle_validation(self, validation):

        if validation["Allowed"]:
            return True

        print("\nTrade Rejected.")
        print(validation["Reason"])

        return False

    def show_performance(self):

        performance = calculate_performance()

        if not performance:
            return

        print("\n========== PERFORMANCE ==========")
        print(f"Total Trades   : {performance['TotalTrades']}")
        print(f"Winning Trades : {performance['WinningTrades']}")
        print(f"Losing Trades  : {performance['LosingTrades']}")
        print(f"Win Rate       : {performance['WinRate']} %")
        print(f"Total P&L      : {performance['TotalPnL']}")
        print(f"Avg Profit     : {performance['AverageProfit']}")
        print(f"Avg Loss       : {performance['AverageLoss']}")
        print(f"Best Trade     : {performance['BestTrade']}")
        print(f"Worst Trade    : {performance['WorstTrade']}")
        print(f"Max Drawdown   : {performance['MaxDrawdown']}")
        print(f"Profit Factor  : {performance['ProfitFactor']}")
        print(f"Expectancy     : {performance['Expectancy']}")
        print(f"Sharpe Ratio   : {performance['SharpeRatio']}")
        print("==================================")

    def show_daily_summary(self):
        """
        Trades placed TODAY only (IST calendar date), scoped from
        completed_trade_history.csv's Date column. Printed at market
        close, in addition to show_performance()'s all-time numbers,
        so the console shows "what happened today" separately from
        "how the bot has done overall".
        """

        daily = calculate_daily_summary()

        print("\n========== DAILY TRADE SUMMARY ==========")
        print(f"Date            : {daily['Date']}")
        print(f"Total Trades    : {daily['TotalTrades']}")

        if daily["TotalTrades"] == 0:
            print("No trades were taken today.")
            print("===========================================")
            return daily

        print(f"  Call Trades   : {daily['CallTrades']}")
        print(f"  Put Trades    : {daily['PutTrades']}")
        print(f"Winning Trades  : {daily['WinningTrades']}")
        print(f"Losing Trades   : {daily['LosingTrades']}")
        print(f"Win Rate        : {daily['WinRate']} %")
        print(f"Total P&L       : {daily['TotalPnL']}")
        print(f"Avg Profit      : {daily['AverageProfit']}")
        print(f"Avg Loss        : {daily['AverageLoss']}")
        print(f"Best Trade      : {daily['BestTrade']}")
        print(f"Worst Trade     : {daily['WorstTrade']}")
        print(f"Max Drawdown    : {daily['MaxDrawdown']}")
        print(f"Profit Factor   : {daily['ProfitFactor']}")
        print(f"Expectancy      : {daily['Expectancy']}")
        print("===========================================")

        return daily

    def show_market_close_summary(self):
        """
        Called once, when check_market_session() first reports the
        market closed for the day (run_continuously()'s exit path).
        Prints today's trades (show_daily_summary) followed by the
        all-time/final tally (show_performance) so both numbers are
        visible together at end of day, not just after whichever
        trade happened to close last. Also sends the same summary to
        Telegram so end-of-day results are visible without needing to
        watch the console (send_notification() already fails safe if
        Telegram isn't configured -- never blocks/crashes the bot).
        """

        print("\n########## END OF DAY REPORT ##########")

        daily = self.show_daily_summary()

        print("\n========== FINAL TRADE SUMMARY (ALL-TIME) ==========")
        self.show_performance()

        print("########################################\n")

        self._send_market_close_telegram_summary(daily)

    def _send_market_close_telegram_summary(self, daily):
        """
        Formats and sends the end-of-day (daily + all-time) summary to
        Telegram. `daily` is the dict already computed by
        show_daily_summary() -- passed in instead of recomputed so the
        console and Telegram versions can never disagree.
        """

        final = calculate_performance() or {}

        if daily["TotalTrades"] == 0:
            message = f"""
    📊 END OF DAY SUMMARY — {daily['Date']}

    No trades were taken today.

    📈 All-Time: {final.get('TotalTrades', 0)} trades | Net P&L: {final.get('TotalPnL', 0)}
    """
        else:
            message = f"""
    📊 END OF DAY SUMMARY — {daily['Date']}

    Trades       : {daily['TotalTrades']} (CE {daily['CallTrades']} / PE {daily['PutTrades']})
    Win / Loss   : {daily['WinningTrades']}W / {daily['LosingTrades']}L ({daily['WinRate']}%)
    Today's P&L  : {daily['TotalPnL']}
    Best / Worst : {daily['BestTrade']} / {daily['WorstTrade']}
    Profit Factor: {daily['ProfitFactor']}

    📈 ALL-TIME TOTAL
    Trades       : {final.get('TotalTrades', 0)}
    Win Rate     : {final.get('WinRate', 0)}%
    Net P&L      : {final.get('TotalPnL', 0)}
    """

        self.send_notification(message)

    def show_equity_curve(self):

        equity = calculate_equity_curve()

        if not equity:
            return

        print("\n========== EQUITY CURVE ==========")

        for i, value in enumerate(equity, start=1):
            print(f"Trade {i} : {value}")

        print("=================================")

    def print_backtest_report(self, backtest):

        print("\n========== BACKTEST REPORT ==========")
        print(f"Total Candles : {backtest['TotalCandles']}")
        print(f"Total Trades  : {backtest['TotalTrades']}")
        print(f"Wins          : {backtest['Wins']}")
        print(f"Losses        : {backtest['Losses']}")
        print(f"EOD Exits     : {backtest['EODExits']}")
        print(f"No Trade      : {backtest['NoTrade']}")
        print(f"Win Rate      : {backtest['WinRate']} %")
        print(f"Profit Factor : {backtest['ProfitFactor']}")
        print(f"Max Drawdown : {backtest['MaximumDrawdown']}")
        print(f"Net P&L       : {backtest['NetPnL']}")
        print(f"Expectancy   : {backtest['Expectancy']}")
        print(f"Sharpe Ratio : {backtest['SharpeRatio']}")
        print("=====================================")

        print("\n========== TRADE LOG ==========")

        for i, trade in enumerate(backtest["TradeLog"], start=1):

            print(
                f"{i}. "
                f"{trade['Signal']} | "
                f"Entry: {trade['Entry']:.2f} | "
                f"Exit: {trade['Exit']:.2f} | "
                f"{trade['Result']} | "
                f"PnL: {trade['PnL']:.2f}"
            )

        print("================================")

    def run_backtest_flow(self, data):

        backtest = run_backtest(data)

        self.print_backtest_report(backtest)

        report_file = save_backtest_report(backtest["TradeLog"])

        print(f"\nBacktest Report Saved : {report_file}")

        return backtest

    def run(self):

        # ==========================================
        # NEW TRADE ENTRY WINDOW — 09:30 to 14:45 IST
        # ==========================================
        ist = ZoneInfo("Asia/Kolkata")
        now = datetime.now(ist)
        now_time = now.time()

        start_hour, start_minute = map(
            int, TRADE_ENTRY_START_TIME.split(":")
        )
        cutoff_hour, cutoff_minute = map(
            int, NO_NEW_ENTRY_AFTER.split(":")
        )

        entry_start_time = dt_time(start_hour, start_minute)
        entry_cutoff_end = dt_time(
            cutoff_hour, cutoff_minute, 59, 999999
        )

        print("\n========== ENTRY WINDOW ==========")
        print(f"Current Time : {now.strftime('%H:%M:%S IST')}")
        print(f"Allowed From : {TRADE_ENTRY_START_TIME} IST")
        print(f"Last Entry   : {NO_NEW_ENTRY_AFTER} IST")
        print("==================================")

        if now_time < entry_start_time:
            print(
                f"[ENTRY BLOCKED] New trades start at "
                f"{TRADE_ENTRY_START_TIME} IST."
            )
            return

        if now_time > entry_cutoff_end:
            print(
                f"[ENTRY BLOCKED] Entry window closed after "
                f"{NO_NEW_ENTRY_AFTER} IST."
            )
            return

        show_features()

        data = self.fetch_market_data()

        data = self.calculate_indicators(data)

        if RUN_BACKTEST:
            print("\nRunning Backtest...")
            self.run_backtest_flow(data)
        else:
            print("\nBacktest Disabled")

        signal, selected_strike = self.generate_trading_signal(data)

        if signal == "NO TRADE":
            print("\nNo Trade Found.")
            return

        if self._is_whipsaw_cooldown_active(signal):
            print("\nTrade Skipped (Whipsaw Cooldown)")
            return

        # Duplicate Trade Protection
        if self.trade_state.is_trade_open():

            current_trade = self.trade_state.get_trade()

            print("\n========== ACTIVE TRADE ==========")
            print(f"Entry     : {current_trade['Entry']}")
            print(f"Target    : {current_trade['Target']}")
            print(f"Stop Loss : {current_trade['StopLoss']}")
            print("==================================")
            print("Trade Already Open")
            print("Skipping New Signal...")

            return

        trade, position, validation = self.manage_risk(
            signal,
            data,
            selected_strike,
        )

        if trade is None:
            print("Unable to calculate premium")
            return

        self.print_trade_details(trade)
        self.print_position_size(position)
        self.print_validation(validation)

        portfolio = portfolio_summary()
        self.print_portfolio(portfolio)

        if not self.handle_validation(validation):
            return

        paper_trade = self.execute_trade_flow(
            signal,
            trade,
            selected_strike,
        )

        if paper_trade is None:
            return

        self.monitor_open_trade(paper_trade)

        self.show_performance()

        self.show_equity_curve()

        show_dashboard()
