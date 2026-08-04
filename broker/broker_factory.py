from broker.paper_broker import PaperBroker
from broker.angelone_broker import AngelOneBroker
from broker.zerodha_broker import ZerodhaBroker


class BrokerFactory:

    AVAILABLE_BROKERS = (
        "PAPER",
        "ANGELONE",
        "ZERODHA",
    )

    @staticmethod
    def create_broker(broker_name):

        broker_name = broker_name.upper().strip()

        if broker_name not in BrokerFactory.AVAILABLE_BROKERS:

            raise ValueError(
                f"""
Unsupported Broker : {broker_name}

Available Brokers:

- PAPER
- ANGELONE
- ZERODHA
"""
            )

        if broker_name == "PAPER":
            return PaperBroker()

        if broker_name == "ANGELONE":
            return AngelOneBroker()

        if broker_name == "ZERODHA":
            return ZerodhaBroker()