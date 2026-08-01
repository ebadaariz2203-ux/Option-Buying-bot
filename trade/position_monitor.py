import time

from paper_trade.paper_trade import monitor_trade
from trade.pnl_engine import get_trade_status


class PositionMonitor:

    def __init__(self, position_manager):

        self.position_manager = position_manager

    def monitor(self, current_price):

        if not self.position_manager.has_position():

            print("\nNo Active Position")

            return "NO POSITION"

        trade = self.position_manager.get_position()

        trade_status = monitor_trade(current_price, trade)

        print("\n========== TRADE MONITOR ==========")

        while trade_status == "OPEN":

            time.sleep(2)

            # Abhi testing ke liye current_price same rahega.
            # Day 85 me live market price use hoga.

            trade_status = monitor_trade(current_price, trade)

            pnl = get_trade_status(
                entry_price=trade["Entry"],
                current_price=current_price,
                quantity=trade.get("Quantity", 1),
            )

            print(f"""
        Current Price : {pnl['CurrentPrice']}
        PnL           : {pnl['PnL']}
        Return        : {pnl['Return']} %
        Status        : {trade_status}
        """)
            
        print("\n========== LIVE POSITION ==========")
        print(f"Entry Price   : {trade['Entry']}")
        print(f"Current Price : {current_price}")
        print(f"PnL           : {pnl['PnL']}")
        print(f"Return        : {pnl['Return']} %")
        print(f"Status        : {trade_status}")
        print("===================================")

        if trade_status in ("TARGET HIT", "STOP LOSS HIT"):

            print("\nClosing Position...")

            self.position_manager.close_position()

            print("Position Closed Successfully.")

        return trade_status