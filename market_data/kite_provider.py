import pandas as pd
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from kiteconnect import KiteConnect

from market_data.data_provider import DataProvider


load_dotenv()


class KiteProvider(DataProvider):

    NIFTY_TOKEN = 256265
    NIFTY_SYMBOL = "NSE:NIFTY 50"

    def __init__(self):

        api_key = os.getenv("KITE_API_KEY")
        access_token = os.getenv("KITE_ACCESS_TOKEN")

        if not api_key or not access_token:
            raise ValueError(
                "KITE_API_KEY or KITE_ACCESS_TOKEN is missing."
            )

        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)

    # ==========================================
    # NIFTY MARKET DATA
    # ==========================================

    def get_market_data(self, interval="5minute", days=2):
        # FIX: interval/days made configurable so the bot can fetch its
        # 15-minute HTF (higher timeframe) confirmation data from the SAME
        # broker/source (Kite) as the 5-minute data, instead of mixing in
        # Yahoo Finance (yfinance) for the 15m leg. Two different data
        # vendors can disagree slightly on OHLC values/timestamps, which was
        # causing the HTF confirmation check to mismatch and skip trades
        # more often than it should.

        ist = ZoneInfo("Asia/Kolkata")

        to_date = datetime.now(ist)
        from_date = to_date - timedelta(days=days)

        candles = self.kite.historical_data(
            instrument_token=self.NIFTY_TOKEN,
            from_date=from_date,
            to_date=to_date,
            interval=interval
        )

        data = pd.DataFrame(candles)

        if data.empty:
            raise Exception("No market data received from Kite.")

        data = data.rename(
            columns={
                "date": "Date",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume"
            }
        )

        data["Date"] = pd.to_datetime(data["Date"])

        data.set_index("Date", inplace=True)

        return data

    # ==========================================
    # NIFTY FUTURES MARKET DATA
    # ==========================================

    def get_nifty_futures_data(self):

        ist = ZoneInfo("Asia/Kolkata")

        today = datetime.now(ist).date()

        # Get all NFO instruments
        instruments = self.kite.instruments("NFO")

        # Find NIFTY FUTURES
        nifty_futures = [
            instrument
            for instrument in instruments
            if instrument["name"] == "NIFTY"
            and instrument["instrument_type"] == "FUT"
            and instrument["expiry"] >= today
        ]

        if not nifty_futures:
            raise ValueError(
                "No NIFTY Futures instrument found."
            )

        # Select nearest expiry
        nearest_future = min(
            nifty_futures,
            key=lambda instrument: instrument["expiry"]
        )

        instrument_token = nearest_future["instrument_token"]

        # Historical data
        to_date = datetime.now(ist)
        from_date = to_date - timedelta(days=2)

        candles = self.kite.historical_data(
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval="5minute"
        )

        data = pd.DataFrame(candles)

        if data.empty:
            raise Exception(
                "No NIFTY Futures data received from Kite."
            )

        data = data.rename(
            columns={
                "date": "Date",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume"
            }
        )

        data["Date"] = pd.to_datetime(data["Date"])

        data.set_index("Date", inplace=True)

        return data

    # ==========================================
    # NIFTY OPTION CHAIN
    # ==========================================

    def get_option_chain(self, spot_price):

        instruments = self.kite.instruments("NFO")

        nifty_options = [
            instrument
            for instrument in instruments
            if instrument["name"] == "NIFTY"
            and instrument["instrument_type"] in ("CE", "PE")
        ]

        if not nifty_options:
            raise ValueError("No NIFTY option instruments found.")

        # ==========================================
        # ATM STRIKE
        # ==========================================

        strikes = [
            instrument["strike"]
            for instrument in nifty_options
        ]

        atm_strike = min(
            strikes,
            key=lambda strike: abs(strike - spot_price)
        )

        # ==========================================
        # SELECT NEAREST EXPIRY
        # ==========================================

        today = datetime.now().date()

        future_expiries = sorted(
            {
                instrument["expiry"]
                for instrument in nifty_options
                if instrument["expiry"] >= today
            }
        )

        if not future_expiries:
            raise ValueError("No valid NIFTY option expiry found.")

        nearest_expiry = future_expiries[0]

        # ==========================================
        # ATM ± 100
        # ==========================================

        strike_range = [
            atm_strike - 100,
            atm_strike - 50,
            atm_strike,
            atm_strike + 50,
            atm_strike + 100,
        ]

        # ==========================================
        # SELECT 5 STRIKES × CE/PE
        # ==========================================

        selected_options = [
            instrument
            for instrument in nifty_options
            if instrument["expiry"] == nearest_expiry
            and instrument["strike"] in strike_range
        ]

        if not selected_options:
            raise ValueError(
                "No NIFTY options found for selected strike range."
            )

        # ==========================================
        # BUILD OPTION SYMBOLS
        # ==========================================

        symbols = [
            f"NFO:{instrument['tradingsymbol']}"
            for instrument in selected_options
        ]

        # ==========================================
        # GET REAL OPTION QUOTES
        # ==========================================

        quote_data = self.kite.quote(symbols)

        # ==========================================
        # BUILD OPTION DATA
        # ==========================================

        option_data = []

        for instrument in selected_options:

            symbol = f"NFO:{instrument['tradingsymbol']}"

            quote = quote_data[symbol]

            bid = 0
            ask = 0

            if quote.get("depth"):

                buy_depth = quote["depth"].get("buy", [])
                sell_depth = quote["depth"].get("sell", [])

                if buy_depth:
                    bid = buy_depth[0]["price"]

                if sell_depth:
                    ask = sell_depth[0]["price"]

            option_data.append(
                {
                    # FIX: tradingsymbol preserved so the bot can re-query
                    # a live LTP for THIS exact contract later, while a
                    # trade is open (needed for real-price monitoring
                    # instead of the old random-walk simulator).
                    "Symbol": instrument["tradingsymbol"],

                    "Strike": instrument["strike"],
                    "Type": instrument["instrument_type"],
                    "OI": quote.get("oi", 0),
                    "Volume": quote.get("volume", 0),
                    "LTP": quote.get("last_price", 0),
                    "Bid": bid,
                    "Ask": ask,
                    "IV": 0,
                }
            )

        # ==========================================
        # CALCULATE CALL OI / PUT OI / PCR
        # ==========================================

        call_oi = sum(
            option["OI"]
            for option in option_data
            if option["Type"] == "CE"
        )

        put_oi = sum(
            option["OI"]
            for option in option_data
            if option["Type"] == "PE"
        )

        if call_oi > 0:
            pcr = put_oi / call_oi
        else:
            pcr = 0

        # ==========================================
        # RETURN EXISTING STRUCTURE
        # ==========================================

        option_chain = {

            "PCR": round(pcr, 2),

            "Call_OI": call_oi,

            "Put_OI": put_oi,

            "ATM_Strike": atm_strike,

            "Strikes": option_data,

            "IsSimulated": False,

            "Selected_Strike": None
        }

        return option_chain

    # ==========================================
    # LIVE LTP (used during trade monitoring)
    # ==========================================

    def get_ltp(self, tradingsymbol, exchange="NFO"):
        """
        NEW METHOD.

        Fetches the current live premium (LTP) for a single option
        contract while a trade is open. This replaces the old
        market_simulator.simulate_price() random-walk that was being
        used to "monitor" open trades — target/SL/trailing-stop/partial
        -exit decisions were previously being made on fake random
        numbers instead of the real market price.

        tradingsymbol : e.g. "NIFTY2582225000CE" (from the "Symbol"
                         field now returned in get_option_chain()).
        """

        symbol = f"{exchange}:{tradingsymbol}"

        quote = self.kite.ltp(symbol)

        if symbol not in quote:
            raise Exception(
                f"No LTP data returned for {symbol}"
            )

        return float(quote[symbol]["last_price"])
