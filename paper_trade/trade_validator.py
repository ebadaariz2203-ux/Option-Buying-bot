def validate_trade(position):

    if position["Lots"] >= 1:

        return {
            "Allowed": True,
            "Reason": "Trade Allowed"
        }

    return {
        "Allowed": False,
        "Reason": "Insufficient Capital"
    }