def validate_trade(position):

    if position["Lots"] < 1:
        return {
            "Allowed": False,
            "Reason": "Insufficient Capital"
        }

    # FIX: previously only "Lots >= 1" was checked here, so
    # calculate_position_size()'s EnoughCapital flag (required_capital
    # <= CAPITAL) was computed but never actually enforced -- a trade
    # sized beyond available capital would still pass validation.
    # This matters more now that RISK_PER_TRADE / lot count can push
    # required capital higher; enforce it explicitly.
    if not position.get("EnoughCapital", True):
        return {
            "Allowed": False,
            "Reason": "Insufficient Capital"
        }

    return {
        "Allowed": True,
        "Reason": "Trade Allowed"
    }