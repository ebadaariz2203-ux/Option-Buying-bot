from trade.trade_state import TradeState


class PositionManager:

    def __init__(self, trade_state: TradeState):

        self.trade_state = trade_state

    def open_position(self, trade):

        self.trade_state.open_trade(trade)

    def close_position(self):

        self.trade_state.close_trade()

    def get_position(self):

        return self.trade_state.get_trade()

    def has_position(self):

        return self.trade_state.is_trade_open()

    def print_position(self):

        position = self.get_position()

        if position is None:

            print("\nNo Active Position")
            return

        print("\n========== ACTIVE POSITION ==========")
        print(f"Signal     : {position['Signal']}")
        print(f"Entry      : {position['Entry']}")
        print(f"Target     : {position['Target']}")
        print(f"Stop Loss  : {position['StopLoss']}")

        if "Strike" in position:
            print(f"Strike     : {position['Strike']}")

        if "OptionType" in position:
            print(f"Option Type: {position['OptionType']}")

        if "Quantity" in position:
            print(f"Quantity   : {position['Quantity']}")

        print("=====================================")