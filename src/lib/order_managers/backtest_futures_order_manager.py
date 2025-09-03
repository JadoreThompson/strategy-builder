from lib.typing import Position
from .demo_futures_order_manager import DemoFuturesOrderManager


class BacktestFuturesOrderManager(DemoFuturesOrderManager):
    """A proxy class that stores the closed positions"""

    def __init__(self, starting_balance = None, leverage = 10):
        super().__init__(starting_balance, leverage)
        self._closed_positions: list[Position] = []

    def login(self) -> bool:
        return True

    def close_position(self, position_id: str, price: float, amount: float) -> bool:
        pos = self._positions.get(position_id, None)
        if pos is None:
            return False

        if amount == pos.current_amount:
            self._closed_positions.append(pos)
        return super().close_position(position_id, price, amount)
