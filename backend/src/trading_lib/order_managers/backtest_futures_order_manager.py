import heapq
import logging
from decimal import Decimal
from pprint import pprint

from core.enums import OrderType, PositionStatus, Side
from core.typing import Position
from trading_lib.typing import MODIFY_SENTINEL, Tick
from utils import get_datetime
from .futures_order_manager import FuturesOrderManager


logger = logging.getLogger(__name__)


class BacktestFuturesOrderManager(FuturesOrderManager):
    def __init__(self, starting_balance: float = 100_000.0, leverage: int = 10):
        super().__init__()

        if starting_balance is None:
            logger.warning("No starting balance provided")

        self._leverage = leverage
        self._balance = Decimal(str(starting_balance))
        self._equity = Decimal("0.0")
        self._margin = Decimal("0.0")
        self._free_margin = self._balance

        self._closed_positions: list[Position] = []

    def login(self) -> bool:
        return True

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
    ) -> str | None:
        if not self._perform_pretrade_risk(amount):
            return None

        pos = self._exchange.open_position(
            instrument,
            side,
            order_type,
            amount,
            limit_price,
            stop_price,
            tp_price,
            sl_price,
        )
        self._positions[pos.position_id] = pos
        return pos.position_id

    def modify_position(
        self,
        position_id: str,
        limit_price: float | None = MODIFY_SENTINEL,
        stop_price: float | None = MODIFY_SENTINEL,
        tp_price: float | None = MODIFY_SENTINEL,
        sl_price: float | None = MODIFY_SENTINEL,
    ) -> bool:
        pos = self._positions.get(position_id)
        if not pos:
            return False

        success, new_pos = self._exchange.modify_position(
            pos, limit_price, stop_price, tp_price, sl_price
        )

        if success:
            self._positions[position_id] = new_pos

        return True

    def close_position(self, position_id: str, amount: Decimal) -> bool:
        """Simulate position close (remove from active positions)."""
        price = self._exchange.last_tick.last
        pos = self._positions.pop(position_id, None)
        if pos is None:
            return False

        if amount > pos.current_amount:
            self._positions[pos.position_id] = pos
            logger.error(
                f"Invalid close amount {amount} is greater than position amount {pos.current_amount}"
            )
            return False

        pos.unrealised_pnl = self._calc_upl(pos, price, pos.current_amount)
        self._margin -= amount

        if amount == pos.current_amount:
            self._equity -= pos.unrealised_pnl
            pos.current_amount = 0

            self._balance += pos.unrealised_pnl
            pos.realised_pnl += pos.unrealised_pnl
            pos.unrealised_pnl = 0.0

            pos.close_price = price
            pos.closed_at = self._exchange.last_tick.time
            pos.status = PositionStatus.CLOSED
            self._closed_positions.append(pos)
        else:
            pnl = self._calc_upl(pos, price, amount)
            self._balance += pnl
            self._equity -= pnl

            pos.realised_pnl += pnl
            pos.current_amount -= amount
            pos.unrealised_pnl = self._calc_upl(pos, price, pos.current_amount)

            self._positions[pos.position_id] = pos

        self._free_margin = self._equity - self._margin
        return True

    def close_all_positions(self) -> None:
        for pos in list(self._positions.values()):
            self.close_position(pos.position_id, pos.current_amount)

    def cancel_position(self, position_id: str) -> bool:
        """Alias for close in backtest context (cancel = remove before fill)."""
        if (
            pos := self._positions.get(position_id)
        ) and pos.status == PositionStatus.PENDING:
            pos = self._positions.pop(pos.position_id)
            self._margin -= pos.current_amount
            self._free_margin = self._equity - self._margin
            pos.status = PositionStatus.CANCELLED
            return True

        return False

    def cancel_all_positions(self) -> None:
        """Remove all active positions."""
        for pos in list(self._positions.values()):
            if pos.status == PositionStatus.PENDING:
                self._positions.pop(pos.position_id)
                self._margin -= pos.current_amount
                self._free_margin = self._equity - self._margin

    def perform_risk_checks(self, tick: Tick) -> bool:
        """
        Updates free margin and performs margin call if
        necessary.

        Args:
            tick (Tick)
        Returns:
            bool: True if there's remaining free margin.
        """
        zero = Decimal("0.0")
        new_equity = zero

        for pos in self._positions.values():
            upnl = self._calc_upl(pos, tick.last, pos.current_amount)
            new_equity += upnl

        self._equity = self._balance + new_equity
        self._free_margin = self._equity - self._margin

        # Closing positions
        if self._free_margin <= zero:
            positions: list[tuple[float, Position]] = []
            for pos in self._positions.values():
                heapq.heappush(positions, (pos.current_amount, pos))

            while self._free_margin <= zero and positions:
                current_amount, pos = positions.pop()

                self._margin -= current_amount
                self._equity -= pos.unrealised_pnl
                self._free_margin = self._equity - self._margin

                pos.realised_pnl += pos.unrealised_pnl
                self._balance += pos.realised_pnl
                pos.unrealised_pnl = zero

                pos.current_amount = zero
                pos.close_price = tick.last
                pos.closed_at = tick.time
                pos.status = PositionStatus.CLOSED
                self._positions.pop(pos.position_id)

        return self._free_margin > zero

    def _perform_pretrade_risk(self, amount: float) -> bool:
        amount = Decimal(str(amount))
        if self._free_margin < amount * self._leverage:
            return False

        self._margin += amount
        self._free_margin -= amount
        return True

    def _calc_upl(self, pos: Position, close_price: float, amount: float):
        total_amount = Decimal(str(amount * self._leverage))
        if pos.order_type == OrderType.MARKET:
            open_price = pos.price
        elif pos.order_type == OrderType.LIMIT:
            open_price = pos.limit_price
        elif pos.order_type == OrderType.STOP:
            open_price = pos.stop_price

        try:
            if pos.side == Side.ASK:
                pct = (open_price - close_price) / open_price
            else:
                pct = (close_price - open_price) / open_price
        except ZeroDivisionError:
            pct = 0.0

        upnl = Decimal(str(pct)) * total_amount
        return upnl
