"""
Option Chain Provider

Currently using simulated option chain.
Real NSE fetch can be added later.
"""


def get_option_chain(nifty_price):

    """
    Main entry point used by bot.py
    """

    atm_strike = int(round(nifty_price / 50) * 50)

    strikes = []

    for strike in [
        atm_strike - 50,
        atm_strike,
        atm_strike + 50
    ]:

        strikes.append(
            {
                "Strike": strike,
                "Type": "CE",
                "OI": 1500000,
                "Volume": 50000
            }
        )

        strikes.append(
            {
                "Strike": strike,
                "Type": "PE",
                "OI": 1700000,
                "Volume": 70000
            }
        )


    option_chain = {

        "PCR": 1.05,

        "Call_OI": 1500000,

        "Put_OI": 1700000,

        "ATM_Strike": atm_strike,

        "Strikes": strikes,

        "IsSimulated": True,

        "Selected_Strike": None
    }


    return option_chain