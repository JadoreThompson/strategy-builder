from abc import abstractmethod
from decimal import Decimal

from core.enums import OrderType, Side
from lib.typing import Position


class FuturesOrderManager:
    def __init__(self):
        self._positions: dict[str, Position] = {}

    @abstractmethod
    def login(self) -> bool: ...

    @abstractmethod
    def open_position(
        self,
        *,
        instrument: str,
        side: Side,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal | None = None,
        limit_price: Decimal | None = None,
        stop_price: Decimal | None = None,
        tp_price: Decimal | None = None,
        sl_price: Decimal | None = None,
    ) -> str | None:
        """
        Returns the position id or None if position 
        couldn't be placed
        """

    @abstractmethod
    def update_position(
        self,
        *,
        position_id: str,
        limit_price: Decimal | None = None,
        stop_price: Decimal | None = None,
        tp_price: Decimal | None = None,
        sl_price: Decimal | None = None,
    ) -> bool: ...

    """Returns whether or not the call was successfull"""

    @abstractmethod
    def close_position(self, position_id: str, price: float, amount: Decimal): ...

    @abstractmethod
    def cancel_position(self, position_id: str): ...

    @abstractmethod
    def cancel_all_positions(self): ...
