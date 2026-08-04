from abc import ABC, abstractmethod


class Broker(ABC):

    @abstractmethod
    def place_order(self, signal, trade):
        pass

    @abstractmethod
    def close_order(self, trade):
        pass

    @abstractmethod
    def get_position(self):
        pass