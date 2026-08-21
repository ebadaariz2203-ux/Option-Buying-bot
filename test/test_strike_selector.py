from strategy.strike_selector import select_best_strike


print("\n========== STRIKE SELECTOR TEST ==========")


# ==========================================
# REAL KITE OPTION DATA
# ==========================================

option_chain = {

    "Strikes": [

        {
            "Strike": 24500,
            "Type": "CE",
            "OI": 6485765,
            "Volume": 116284675,
            "LTP": 171.40,
            "Bid": 171.15,
            "Ask": 171.40,
            "IV": 0,
        },

        {
            "Strike": 24550,
            "Type": "CE",
            "OI": 5994495,
            "Volume": 150441720,
            "LTP": 135.15,
            "Bid": 134.35,
            "Ask": 134.75,
            "IV": 0,
        },

        {
            "Strike": 24600,
            "Type": "CE",
            "OI": 21616400,
            "Volume": 319011550,
            "LTP": 103.85,
            "Bid": 103.60,
            "Ask": 103.90,
            "IV": 0,
        },

        {
            "Strike": 24650,
            "Type": "CE",
            "OI": 12379185,
            "Volume": 152014395,
            "LTP": 76.85,
            "Bid": 76.80,
            "Ask": 76.95,
            "IV": 0,
        },

        {
            "Strike": 24700,
            "Type": "CE",
            "OI": 16097640,
            "Volume": 167077430,
            "LTP": 54.90,
            "Bid": 54.85,
            "Ask": 55.00,
            "IV": 0,
        },

        {
            "Strike": 24500,
            "Type": "PE",
            "OI": 23051405,
            "Volume": 226683015,
            "LTP": 34.50,
            "Bid": 34.45,
            "Ask": 34.55,
            "IV": 0,
        },

        {
            "Strike": 24550,
            "Type": "PE",
            "OI": 18324800,
            "Volume": 214487325,
            "LTP": 48.80,
            "Bid": 49.20,
            "Ask": 49.30,
            "IV": 0,
        },

        {
            "Strike": 24600,
            "Type": "PE",
            "OI": 28275585,
            "Volume": 283041005,
            "LTP": 67.35,
            "Bid": 67.15,
            "Ask": 67.30,
            "IV": 0,
        },

        {
            "Strike": 24650,
            "Type": "PE",
            "OI": 8465405,
            "Volume": 86804185,
            "LTP": 90.75,
            "Bid": 90.65,
            "Ask": 90.85,
            "IV": 0,
        },

        {
            "Strike": 24700,
            "Type": "PE",
            "OI": 6891300,
            "Volume": 68425045,
            "LTP": 119.00,
            "Bid": 118.80,
            "Ask": 119.00,
            "IV": 0,
        },
    ]
}


# ==========================================
# BUY CALL
# ==========================================

call_result = select_best_strike(
    "BUY CALL",
    option_chain
)

print("\nBUY CALL")
print("Selected Strike :", call_result["Strike"])
print("Option Type     :", call_result["Type"])
print("Volume          :", call_result["Volume"])


# ==========================================
# BUY PUT
# ==========================================

put_result = select_best_strike(
    "BUY PUT",
    option_chain
)

print("\nBUY PUT")
print("Selected Strike :", put_result["Strike"])
print("Option Type     :", put_result["Type"])
print("Volume          :", put_result["Volume"])