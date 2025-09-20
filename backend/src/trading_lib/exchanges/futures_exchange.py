from abc import abstractmethod
from decimal import Decimal

from core.enums import OrderType, Side
from core.typing import Position
from trading_lib.typing import MODIFY_SENTINEL#, Position
from .exchange import Exchange


class FuturesExchange(Exchange):
    """Abstract base class for a futures trading exchange."""

    @abstractmethod
    def open_position(
        self,
        instrument: str,
        side: Side,
        order_type: OrderType,
        amount: Decimal,
        limit_price: float | None = None,
        stop_price: float | None = None,
        tp_price: float | None = None,
        sl_price: float | None = None,
    ) -> Position | None: ...

    @abstractmethod
    def modify_position(
        self,
        position: Position,
        limit_price: float | None = MODIFY_SENTINEL,
        stop_price: float | None = MODIFY_SENTINEL,
        tp_price: float | None = MODIFY_SENTINEL,
        sl_price: float | None = MODIFY_SENTINEL,
    ) -> tuple[bool, Position]: ...

    @abstractmethod
    def close_position(
        self, position: Position, price: Decimal, amount: Decimal
    ) -> tuple[bool, Position]: ...

    @abstractmethod
    def close_all_positions(self) -> None: ...

    @abstractmethod
    def cancel_position(self, position_id: str) -> bool: ...

    @abstractmethod
    def cancel_all_positions(self) -> None: ...
