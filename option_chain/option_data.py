
def calculate_atm_strike(nifty_price):

    return round(nifty_price / 50) * 50

def select_strike(signal, atm_strike):

    if signal == "BUY CALL":
        return atm_strike

    elif signal == "BUY PUT":
        return atm_strike

    return None

def get_option_chain(nifty_price):

    atm_strike = calculate_atm_strike(nifty_price)

    option = {
        "PCR": 1.05,
        "Call_OI": 1500000,
        "Put_OI": 1700000,
        "ATM_Strike": atm_strike,
        "Selected_Strike": None,

        "Strikes": [
            {"Strike": atm_strike - 50, "Type": "CE", "OI": 1800000, "Volume": 85000},
            {"Strike": atm_strike,      "Type": "CE", "OI": 1500000, "Volume": 50000},
            {"Strike": atm_strike + 50, "Type": "CE", "OI": 1200000, "Volume": 25000},

            {"Strike": atm_strike - 50, "Type": "PE", "OI": 1400000, "Volume": 30000},
            {"Strike": atm_strike,      "Type": "PE", "OI": 1700000, "Volume": 90000},
            {"Strike": atm_strike + 50, "Type": "PE", "OI": 1600000, "Volume": 60000},
        ]
    }

    return option
