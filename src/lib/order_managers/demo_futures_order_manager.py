import logging
from uuid import uuid4

from core.enums import OrderType, PositionStatus, Side, StrategyType
from lib.typing import Position
from lib.utils import calc_price_change
from utils import get_datetime
from .futures_order_manager import FuturesOrderManager


logger = logging.getLogger(__name__)


# TODO: Fix PNL issue
class DemoFuturesOrderManager(FuturesOrderManager):
    def __init__(self, starting_balance: float | None = None):
        super().__init__()
        if starting_balance is None:
            logger.warning("No starting balance provided")
        self._balance = starting_balance

    def login(self) -> bool:
        if self._balance is None:
            raise ValueError("Starting balance not provided.")
        return True

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
        pos_id = str(uuid4())
        pos = Position(
            id=pos_id,
            instrument=instrument,
            side=side,
            order_type=order_type,
            starting_amount=amount,
            price=price,
            limit_price=limit_price,
            stop_price=stop_price,
            tp_price=tp_price,
            sl_price=sl_price,
            status=(
                PositionStatus.OPEN
                if order_type == OrderType.MARKET
                else PositionStatus.PENDING
            ),
        )
        self._positions[pos_id] = pos
        self._balance -= amount
        return pos_id

    def update_position(
        self,
        *,
        position_id: str,
        limit_price: float | None = None,
        stop_price: float | None = None,
        tp_price: float | None = None,
        sl_price: float | None = None,
    ) -> bool:
        pos = self._positions.get(position_id)
        if not pos:
            return False

        updated = Position(
            id=pos.id,
            instrument=pos.instrument,
            side=pos.side,
            order_type=pos.order_type,
            starting_amount=pos.starting_amount,
            price=pos.price,
            limit_price=limit_price if limit_price is not None else pos.limit_price,
            stop_price=stop_price if stop_price is not None else pos.stop_price,
            tp_price=tp_price if tp_price is not None else pos.tp_price,
            sl_price=sl_price if sl_price is not None else pos.sl_price,
        )
        self._positions[position_id] = updated
        return True

    def close_position(self, position_id: str, price: float, amount: float) -> bool:
        """Simulate position close (remove from active positions)."""
        pos = self._positions.pop(position_id, None)
        if pos is None:
            return False

        if amount > pos.current_amount:
            self._positions[pos.id] = pos
            return False

        open_price = pos.price or pos.limit_price or pos.stop_price
        k = -1 if pos.side == Side.ASK else 1
        price_change = calc_price_change(open_price, price)
        pos.unrealised_pnl = k * pos.current_amount * price_change

        if amount == pos.current_amount:
            pos.current_amount = 0
            self._balance += pos.unrealised_pnl
            pos.realised_pnl += pos.unrealised_pnl
            pos.unrealised_pnl = 0.0
            pos.close_price = price
            pos.closed_at = get_datetime()
            pos.status = PositionStatus.CLOSED
        else:
            pos.current_amount -= amount
            pnl = k * amount * price_change
            self._balance += pnl
            pos.realised_pnl += pnl

            if pos.unrealised_pnl < 0.0:
                pos.unrealised_pnl += pnl
            else:
                pos.unrealised_pnl -= pnl

            self._positions[pos.id] = pos

        return True

    def cancel_position(self, position_id: str) -> bool:
        """Alias for close in backtest context (cancel = remove before fill)."""
        if (
            pos := self._positions.get(position_id)
        ) and pos.status == PositionStatus.PENDING:
            return bool(self._positions.pop(pos.id))

    def cancel_all_positions(self) -> None:
        """Remove all active positions."""
        for pos in list(self._positions.values()):
            if pos.status == PositionStatus.PENDING:
                self._positions.pop(pos.id)
