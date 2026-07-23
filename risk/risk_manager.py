from config import ATR_MULTIPLIER, RISK_REWARD
def calculate_trade(entry_price, atr):
    """
    Calculate Entry, ATR Based Stop Loss and Target
    """

    risk = atr * ATR_MULTIPLIER

    stop_loss = round(entry_price - risk, 2)

    target = round(entry_price + (risk * RISK_REWARD), 2)

    return {
    "Entry": round(entry_price, 2),
    "ATR": round(atr, 2),
    "ATRMultiplier": ATR_MULTIPLIER,
    "RiskReward": RISK_REWARD,
    "StopLoss": stop_loss,
    "Target": target
}
    


def calculate_pnl(entry_price, exit_price):

    pnl = round(exit_price - entry_price, 2)

    pnl_percent = round((pnl / entry_price) * 100, 2)

    return {
        "Entry": entry_price,
        "Exit": exit_price,
        "PnL": pnl,
        "PnLPercent": pnl_percent
    }