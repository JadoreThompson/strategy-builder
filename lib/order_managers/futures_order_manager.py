from abc import abstractmethod


class FuturesOrderManager:
    def __init__(self):
        self._positions = {}

    @abstractmethod
    def login(self) -> bool: ...

    @abstractmethod
    def open_position(self): ...

    @abstractmethod
    def close_position(self): ...

    @abstractmethod
    def cancel_position(self): ...