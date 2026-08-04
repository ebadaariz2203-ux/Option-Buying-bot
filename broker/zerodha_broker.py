from broker.broker import Broker


class ZerodhaBroker(Broker):

    def place_order(self, signal, trade):
        print("Zerodha Broker - Place Order")
        raise NotImplementedError("Zerodha integration pending.")

    def close_order(self, trade):
        print("Zerodha Broker - Close Order")
        raise NotImplementedError("Zerodha integration pending.")

    def get_position(self):
        print("Zerodha Broker - Get Position")
        raise NotImplementedError("Zerodha integration pending.")