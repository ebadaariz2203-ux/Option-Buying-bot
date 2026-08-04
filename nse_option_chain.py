"""
NSE India Option Chain Fetcher
--------------------------------
Fetches live option chain data (PCR, OI, ATM premium) from NSE India's
public API. No API key or broker account needed.

Usage:
    from nse_option_chain import get_option_chain
    option = get_option_chain(nifty_price=22150)
"""

import requests
import time


NSE_BASE_URL = "https://www.nseindia.com"
NSE_OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}


def _get_nse_session():
    """
    NSE blocks requests without a valid session cookie.
    We first hit the homepage to collect cookies, then use
    the same session for the API call.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    # Homepage visit sets the cookies NSE checks for on the API call
    session.get(NSE_BASE_URL, timeout=5)
    time.sleep(1)  # small delay avoids getting blocked

    return session


def fetch_raw_option_chain(symbol="NIFTY", retries=3):
    """
    Fetches raw option chain JSON from NSE.
    Retries a few times since NSE sometimes rate-limits/blocks.
    """
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    print("Using file:", __file__)
    print("URL:", url)  
    for attempt in range(retries):
        try:
            session = _get_nse_session()

            response = session.get(url, timeout=5)

            print("Using file:", __file__)
            print("Requested URL:", url)
            print("Final URL:", response.url)
            print("Status:", response.status_code)
            print("Response Headers:", response.headers)
            print("Response Text:", response.text[:300])

            if response.status_code == 200:
                return response.json()

            print(f"NSE API returned status {response.status_code}, retrying...")

        except requests.exceptions.RequestException as e:
            print(f"NSE API request failed: {e}, retrying...")

        time.sleep(2)

    raise Exception("Failed to fetch NSE option chain after retries")


def calculate_atm_strike(spot_price, strike_step=50):
    return round(spot_price / strike_step) * strike_step


def get_option_chain(nifty_price):
    """
    Returns a cleaned option chain dict, structured the same way
    your existing option_chain/option_data.py expects — so you can
    drop this in as a direct replacement for get_option_chain().
    """
    raw = fetch_raw_option_chain("NIFTY")

    records = raw["records"]["data"]
    atm_strike = calculate_atm_strike(nifty_price)

    total_call_oi = 0
    total_put_oi = 0
    strikes = []

    for row in records:
        strike_price = row.get("strikePrice")

        if "CE" in row:
            ce = row["CE"]
            total_call_oi += ce.get("openInterest", 0)
            strikes.append({
                "Strike": strike_price,
                "Type": "CE",
                "OI": ce.get("openInterest", 0),
                "Volume": ce.get("totalTradedVolume", 0),
                "LTP": ce.get("lastPrice", 0),   # <-- real premium here
                "IV": ce.get("impliedVolatility", 0),
            })

        if "PE" in row:
            pe = row["PE"]
            total_put_oi += pe.get("openInterest", 0)
            strikes.append({
                "Strike": strike_price,
                "Type": "PE",
                "OI": pe.get("openInterest", 0),
                "Volume": pe.get("totalTradedVolume", 0),
                "LTP": pe.get("lastPrice", 0),   # <-- real premium here
                "IV": pe.get("impliedVolatility", 0),
            })

    pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 0

    return {
        "PCR": pcr,
        "Call_OI": total_call_oi,
        "Put_OI": total_put_oi,
        "ATM_Strike": atm_strike,
        "Strikes": strikes,
    }


def get_atm_premium(option_chain, atm_strike, option_type):
    """
    Helper: pulls out the real LTP (premium) for the ATM strike,
    so you can replace the hardcoded entry_price = 180.00 in bot.py.
    """
    for strike in option_chain["Strikes"]:
        if strike["Strike"] == atm_strike and strike["Type"] == option_type:
            return strike["LTP"]

    return None


if __name__ == "__main__":
    # Quick test
    option = get_option_chain(nifty_price=22150)

    print("PCR:", option["PCR"])
    print("Call OI:", option["Call_OI"])
    print("Put OI:", option["Put_OI"])
    print("ATM Strike:", option["ATM_Strike"])

    atm_ce_premium = get_atm_premium(option, option["ATM_Strike"], "CE")
    print("ATM CE Premium:", atm_ce_premium)
