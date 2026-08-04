from broker.broker import Broker
from paper_trade.paper_trade import execute_paper_trade


class PaperBroker(Broker):

    def __init__(self):

        self.current_position = None

    def place_order(self, signal, trade):

        paper_trade = execute_paper_trade(signal, trade)

        if paper_trade is None:
            # execute_paper_trade returns None when there isn't enough
            # available balance to lock -- don't crash, just skip the trade.
            return None

        paper_trade["Status"] = "OPEN"

        return paper_trade

    def close_order(self):
     
        print("\nPaper Trade Closed")

    def get_position(self):

        return None