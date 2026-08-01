
"""
Portfolio Manager
Maintains Virtual Trading Balance
"""

from config.settings import CAPITAL

balance = CAPITAL

def get_balance():
    """
    Returns current balance.
    """

    return balance

def get_available_balance():
    """
    Returns available balance.
    """

    return balance - locked_capital

def update_balance(pnl):
    """
    Updates wallet balance.
    """

    global balance

    balance += pnl

    return balance

def lock_capital(amount):
    """
    Locks capital for trade.
    """

    global locked_capital

    if amount > get_available_balance():
        return False

    locked_capital += amount

    return True

def unlock_capital(amount):
    """
    Unlocks capital after trade.
    """

    global locked_capital

    locked_capital -= amount

    if locked_capital < 0:
        locked_capital = 0


def reset_portfolio():
    """
    Reset Portfolio Balance
    """

    global balance

    balance = CAPITAL  
    locked_capital = 0 

def portfolio_summary():
    """
    Returns complete portfolio details.
    """

    return {
        "InitialCapital": CAPITAL,
        "CurrentBalance": balance,
        "Profit": round(balance - CAPITAL, 2),
        "ReturnPercent": round(((balance - CAPITAL) / CAPITAL) * 100, 2)
    }

