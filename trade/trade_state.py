"""
Trade State Manager
"""

class TradeState:

    def __init__(self):
        self.trade_open = False
        self.current_trade = None

    def open_trade(self, trade):
        self.trade_open = True
        self.current_trade = trade

    def close_trade(self):
        self.trade_open = False
        self.current_trade = None

    def is_trade_open(self):
        return self.trade_open

    def get_trade(self):
        return self.current_trade


# ---------- Temporary Testing ----------
