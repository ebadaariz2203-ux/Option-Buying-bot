from broker.broker import Broker


class AngelOneBroker(Broker):

    def place_order(self, signal, trade):
        print("Angel One Broker - Place Order")
        raise NotImplementedError("Angel One integration pending.")

    def close_order(self, trade):
        print("Angel One Broker - Close Order")
        raise NotImplementedError("Angel One integration pending.")

    def get_position(self):
        print("Angel One Broker - Get Position")
        raise NotImplementedError("Angel One integration pending.")