from abc import abstractmethod

from core.enums import OrderType, Side


class SpotOrderManager:
    def __init__(self):
        self._orders = {}

    @abstractmethod
    def login(self) -> bool: ...

    @abstractmethod
    def place_order(
        self,
        *,
        instrument: str,
        side: Side,
        order_type: OrderType,
        amount: float,
        price: float | None = None,
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> str: ...

    """Returns the order Id"""

    @abstractmethod
    def update_order(
        self,
        *,
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> bool: ...

    """Returns whether or not the call was successfull"""

    @abstractmethod
    def cancel_order(self, order_id: str): ...

    @abstractmethod
    def cancel_all_orders(self): ...
