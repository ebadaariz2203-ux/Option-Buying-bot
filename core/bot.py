import time
from datetime import datetime, time as dt_time
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

from portfolio.portfolio_manager import portfolio_summary


# ============================================================
# PNL / TRADE STATUS
# ============================================================

from trade.pnl_engine import get_trade_status


# ============================================================
# PRICING
# ============================================================

from pricing.dynamic_option_price import DynamicOptionPricing


# ============================================================
# ANALYTICS
# ============================================================

from analytics.performance import calculate_performance
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

                    break

                # =================================
                # TRADING CYCLE
                # =================================

                print("\nRunning Trading Cycle...\n")

                self.run()

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
        # ===============================
        if market_regime == "CHOPPY":

            print("\nMarket is Choppy")
            print("Trade Skipped")

            return "NO TRADE", None

        # ===============================
        # FIX: strong_trend and HTF-confirmation used to BOTH be hard
        # AND gates (on top of the CHOPPY check, the EMA/RSI/PCR signal,
        # the VWAP confirmation, and the contra-trend block below) --
        # a 5-6 stage AND-chain that was almost impossible to pass
        # together, causing zero trades across multiple sessions.
        #
        # These two are now scored: SIGNAL_CONFIRMATIONS_REQUIRED (in
        # config/settings.py) controls how many of the 2 must pass.
        # Default = 2 (both required) preserves the exact old strict
        # behaviour. Set it to 1 in settings.py if logs show this pair
        # is what's most often blocking trades.
        # ===============================

        confirmations_passed = sum([strong_trend, htf_confirmed])

        print("\n========== CONFLUENCE CHECK ==========")
        print(f"Strong Trend    : {strong_trend}")
        print(f"HTF Confirmed   : {htf_confirmed}")
        print(f"Passed          : {confirmations_passed} / 2")
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
        paper_trade["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        """
        NEW METHOD.

        Fetches the real current option premium for the open trade via
        the active data provider's Kite LTP call. Replaces the old
        market_simulator.simulate_price() random walk that
        monitor_open_trade() used to rely on.

        Falls back to the trade's own Entry price (a safe neutral
        value that won't falsely trigger target/SL/break-even) if the
        Symbol is missing or the LTP call fails transiently.
        """

        symbol = trade.get("Symbol")

        if not symbol:
            logger.warning(
                "Trade has no Symbol stored - falling back to Entry "
                "price for monitoring."
            )
            return trade["Entry"]

        try:
            return self.data_provider.get_ltp(symbol)

        except Exception as e:
            logger.error(
                f"LTP fetch failed for {symbol}: {e}. "
                f"Using last known Entry price as a safe fallback for "
                f"this tick."
            )
            return trade["Entry"]

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

        print("\n========== TRADE MONITOR ==========")

        while self.position_manager.has_position():

            current_price = self.get_live_premium(trade)

            # ==========================================
            # EOD FORCE EXIT
            # ==========================================

            if is_eod_exit_time():

                print("\n=================================")
                print("      EOD FORCE EXIT")
                print("=================================")

                close_result = close_paper_trade(
                    trade=trade,
                    exit_price=current_price,
                    exit_reason="EOD EXIT",
                    realized_pnl=realized_pnl,
                )

                if close_result:

                    print(f"Entry : {trade['Entry']}")
                    print(f"Exit  : {close_result['ExitPrice']}")
                    print(f"Partial P&L : {close_result.get('PartialPnL', 0)}")
                    print(f"Final P&L   : {close_result.get('FinalPnL', 0)}")
                    print(f"Total P&L   : {close_result['PnL']}")
                    print(f"Return      : {close_result['PnLPercent']} %")

                    save_trade_history({
                        "Time": trade["Time"],
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

                print("EOD Position Closed Successfully.")

                return

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
                logger.debug(
                    f"Break Even / Trailing SL Updated: "
                    f"{old_sl} -> {trade['StopLoss']}"
                )

            # ==========================================
            # DISPLAY TRADE STATUS
            # ==========================================

            print("\n----------------------------")
            print(f"Entry         : {trade['Entry']}")
            print(f"Current Price : {round(current_price, 2)}")
            print(f"Stop Loss     : {trade['StopLoss']}")
            print(f"Target        : {trade['Target']}")
            print(f"Quantity      : {trade['Quantity']}")
            print(f"Realized P&L  : {round(realized_pnl, 2)}")

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

                partial_pnl = round(
                    (current_price - trade["Entry"]) * exit_qty,
                    2
                )

                realized_pnl += partial_pnl

                print("\n=================================")
                print("      PARTIAL PROFIT BOOKING")
                print("=================================")

                print(f"Entry Price        : {trade['Entry']}")
                print(f"Partial Exit Price : {current_price}")
                print(f"Exit Quantity      : {exit_qty}")
                print(f"Remaining Quantity : {remaining_qty}")
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

                print("\n[TARGET HIT] Target Achieved!")

                close_result = close_paper_trade(
                    trade=trade,
                    exit_price=current_price,
                    exit_reason="TARGET HIT",
                    realized_pnl=realized_pnl,
                )

                if close_result:

                    print("\n========== TARGET RESULT ==========")
                    print(f"Entry Price     : {trade['Entry']}")
                    print(f"Exit Price      : {close_result['ExitPrice']}")
                    print(f"Partial P&L     : {close_result.get('PartialPnL', 0)}")
                    print(f"Final P&L       : {close_result.get('FinalPnL', 0)}")
                    print(f"Total P&L       : {close_result['PnL']}")
                    print(f"Return          : {close_result['PnLPercent']} %")
                    print("===================================")

                    save_trade_history({
                        "Time": trade["Time"],
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

                print("Target Position Closed Successfully.")

                return

            if trade_status == "STOP LOSS HIT":

                print("\n[STOP LOSS] Stop Loss Triggered!")

                close_result = close_paper_trade(
                    trade=trade,
                    exit_price=current_price,
                    exit_reason="STOP LOSS HIT",
                    realized_pnl=realized_pnl,
                )

                if close_result:

                    print("\n========== STOP LOSS RESULT ==========")
                    print(f"Entry Price     : {trade['Entry']}")
                    print(f"Exit Price      : {close_result['ExitPrice']}")
                    print(f"Partial P&L     : {close_result.get('PartialPnL', 0)}")
                    print(f"Final P&L       : {close_result.get('FinalPnL', 0)}")
                    print(f"Total P&L       : {close_result['PnL']}")
                    print(f"Return          : {close_result['PnLPercent']} %")
                    print("======================================")

                    save_trade_history({
                        "Time": trade["Time"],
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

                print("Stop Loss Position Closed Successfully.")

                return

            # ==========================================
            # TRADE STILL OPEN
            # ==========================================

            print("\nTrade Status : OPEN")

            pnl_status = get_trade_status(
                entry_price=trade["Entry"],
                current_price=current_price,
                quantity=trade["Quantity"]
            )

            print(f"P&L : {pnl_status}")

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
        # ENTRY CUTOFF — no fresh trades too close to close
        # ==========================================

        ist = ZoneInfo("Asia/Kolkata")
        now_time = datetime.now(ist).time()

        cutoff_hour, cutoff_minute = map(
            int, NO_NEW_ENTRY_AFTER.split(":")
        )
        cutoff_time = dt_time(cutoff_hour, cutoff_minute)

        if now_time >= cutoff_time:

            print(
                f"\nToo close to market close "
                f"(after {NO_NEW_ENTRY_AFTER} IST) — "
                f"no fresh entries taken this cycle."
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
