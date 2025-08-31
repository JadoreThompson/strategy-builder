from abc import abstractmethod

from core.enums import OrderType, Side


class FuturesOrderManager:
    def __init__(self):
        self._positions = {}

    @abstractmethod
    def login(self) -> bool: ...

    @abstractmethod
    def open_position(
        self,
        *,
        instrument: str,
        side: Side,
        order_type: OrderType,
        amount: float,
        price: float | None = None,
        limit_price: float | None = None,
        stop_price: float | None = None,
        tp_price: float | None = None,
        sl_price: float | None = None,
    ) -> str:
        """Returns the position id"""

    @abstractmethod
    def update_position(
        self,
        *,
        limit_price: float | None = None,
        stop_price: float | None = None,
        tp_price: float | None = None,
        sl_price: float | None = None,
    ) -> bool: ...
    """Returns whether or not the call was successfull"""

    @abstractmethod
    def close_position(self, position_id: str): ...

    @abstractmethod
    def cancel_position(self, position_id: str): ...

    @abstractmethod
    def cancel_all_position(self): ...
