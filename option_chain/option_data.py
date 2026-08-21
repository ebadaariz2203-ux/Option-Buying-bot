"""
Real NSE Option Chain Provider

Fetches real NIFTY option-chain data
for paper trading.
"""

import requests
import time


NSE_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"


def get_nse_session():

    session = requests.Session()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/option-chain",
    }

    session.headers.update(headers)

    # First visit NSE homepage to establish cookies
    session.get(
        "https://www.nseindia.com",
        timeout=10
    )

    time.sleep(1)

    return session


def fetch_real_option_chain():

    session = get_nse_session()

    response = session.get(
        NSE_URL,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def get_option_chain(spot_price):

    """
    Fetch real NIFTY option-chain data.

    spot_price:
        Current NIFTY spot price from market-data provider.
    """

    try:

        data = fetch_real_option_chain()

        records = data["records"]

        option_data = records["data"]

        strikes = []

        for item in option_data:

            strike_price = item.get("strikePrice")

            ce = item.get("CE")
            pe = item.get("PE")

            # -------------------------
            # CALL
            # -------------------------

            if ce:

                strikes.append(
                    {
                        "Strike": strike_price,
                        "Type": "CE",
                        "OI": ce.get("openInterest", 0),
                        "Volume": ce.get("totalTradedVolume", 0),
                        "LTP": ce.get("lastPrice", 0),
                        "Bid": ce.get("bidprice", 0),
                        "Ask": ce.get("askPrice", 0),
                        "IV": ce.get("impliedVolatility", 0),
                    }
                )

            # -------------------------
            # PUT
            # -------------------------

            if pe:

                strikes.append(
                    {
                        "Strike": strike_price,
                        "Type": "PE",
                        "OI": pe.get("openInterest", 0),
                        "Volume": pe.get("totalTradedVolume", 0),
                        "LTP": pe.get("lastPrice", 0),
                        "Bid": pe.get("bidprice", 0),
                        "Ask": pe.get("askPrice", 0),
                        "IV": pe.get("impliedVolatility", 0),
                    }
                )

        # -------------------------
        # PCR
        # -------------------------

        total_call_oi = sum(
            item["OI"]
            for item in strikes
            if item["Type"] == "CE"
        )

        total_put_oi = sum(
            item["OI"]
            for item in strikes
            if item["Type"] == "PE"
        )

        if total_call_oi > 0:

            pcr = round(
                total_put_oi / total_call_oi,
                2
            )

        else:

            pcr = 0

        # -------------------------
        # ATM STRIKE
        # -------------------------

        atm_strike = min(
            [item["Strike"] for item in strikes],
            key=lambda strike: abs(
                strike - spot_price
            )
        )

        # -------------------------
        # Return Structure
        # -------------------------

        option_chain = {

            "PCR": pcr,

            "Call_OI": total_call_oi,

            "Put_OI": total_put_oi,

            "ATM_Strike": atm_strike,

            "Strikes": strikes,

            "IsSimulated": False,

            "Selected_Strike": None
        }

        return option_chain

    except Exception as e:

        print(
            f"\n[OPTION CHAIN ERROR] {e}"
        )

        return None