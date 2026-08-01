import uuid

ORDER_PENDING = "PENDING"
ORDER_FILLED = "FILLED"
ORDER_REJECTED = "REJECTED"
ORDER_CANCELLED = "CANCELLED"
class OrderManager:

    def __init__(self, broker):

        self.broker = broker

    def generate_order_id(self):

        return str(uuid.uuid4())[:8].upper()

    def place_order(self, signal, trade):

        order = self.broker.place_order(signal, trade)

        order["OrderID"] = self.generate_order_id()

        order["Status"] = ORDER_PENDING

        # Paper Broker me order instantly execute hota hai
        order["Status"] = ORDER_FILLED

        return order

    def close_order(self):

        position = self.broker.get_position()

        if position is None:
            return

        position["Status"] = ORDER_CANCELLED

        self.broker.close_order()

    def get_position(self):

        return self.broker.get_position()

    def get_order_status(self, order):

        return order.get("Status", "UNKNOWN")