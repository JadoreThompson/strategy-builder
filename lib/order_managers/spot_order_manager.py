from abc import abstractmethod


class SpotOrderManager:
    def __init__(self):
        self._orders = {}

    @abstractmethod
    def login(self) -> bool: ...

    @abstractmethod
    def place_order(self): ...

    @abstractmethod
    def cancel_order(self): ...