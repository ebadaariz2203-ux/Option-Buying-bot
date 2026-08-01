class Broker:

    def place_order(self, signal, trade):
        raise NotImplementedError

    def close_order(self, trade):
        raise NotImplementedError

    def get_position(self):
        raise NotImplementedError