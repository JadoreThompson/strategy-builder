from uuid import uuid4
from .futures_order_manager import FuturesOrderManager


class DemoFuturesOrderManager(FuturesOrderManager):
    def open_position(
        self,
        *,
        instrument,
        side,
        order_type,
        amount,
        price=None,
        limit_price=None,
        stop_price=None,
        tp_price=None,
        sl_price=None,
    ):
        pos = locals()
        pos.pop("self")

        pos_id = uuid4()
        self._positions[pos_id] = pos

    def close_position(self, position_id):
        self._positions.pop(position_id, None)
