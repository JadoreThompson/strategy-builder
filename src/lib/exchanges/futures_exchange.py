from abc import abstractmethod
from decimal import Decimal

from core.enums import OrderType, Side
from lib.typing import MODIFY_SENTINEL, Position
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
        price: Decimal | None = None,
        limit_price: Decimal | None = None,
        stop_price: Decimal | None = None,
        tp_price: Decimal | None = None,
        sl_price: Decimal | None = None,
    ) -> Position | None: ...

    @abstractmethod
    def modify_position(
        self,
        position: Position,
        limit_price: Decimal | None = MODIFY_SENTINEL,
        stop_price: Decimal | None = MODIFY_SENTINEL,
        tp_price: Decimal | None = MODIFY_SENTINEL,
        sl_price: Decimal | None = MODIFY_SENTINEL,
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
