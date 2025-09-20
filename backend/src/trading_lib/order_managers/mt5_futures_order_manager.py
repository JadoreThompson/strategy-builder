import logging
from decimal import Decimal

import MetaTrader5 as mt5
from kafka import KafkaProducer

from config import KAFKA_HOST, KAFKA_PORT, KAFKA_POSITIONS_LOGGER_TOPIC
from core.events import CoreEvent, PositionEvent
from core.enums import CoreEventType, OrderType, PositionStatus, Side
from core.typing import Position
from trading_lib.typing import MODIFY_SENTINEL
from .futures_order_manager import FuturesOrderManager


logger = logging.getLogger(__name__)


class MT5FuturesOrderManager(FuturesOrderManager):
    """
    Manages orders and positions for the MetaTrader 5 platform.
    This class communicates with the MT5 terminal through the MT5FuturesExchange,
    synchronizes account state, and manages a local cache of positions.
    """

    def __init__(self, user_id: str, version_id: str):
        super().__init__()
        self._account_info = None
        self._producer = KafkaProducer(
            bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
        )
        self._user_id = user_id
        self._version_id = version_id

    def login(self) -> bool:
        is_logged_in = self._exchange.login()
        if is_logged_in:
            self._update_account_info()
            self._sync_positions()
        return is_logged_in

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
        if pos:
            self._positions[pos.position_id] = pos
            self._producer.send(
                KAFKA_POSITIONS_LOGGER_TOPIC,
                CoreEvent[PositionEvent](
                    event_type=CoreEventType.POSITION_EVENT,
                    data=PositionEvent(
                        type="new",
                        user_id=self._user_id,
                        version_id=self._version_id,
                        position=pos,
                    ),
                )
                .model_dump_json()
                .encode(),
            )
            return pos.position_id
        return None

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
            logger.error(f"Position with ID {position_id} not found for modification.")
            return False

        success, updated_pos = self._exchange.modify_position(
            pos, limit_price, stop_price, tp_price, sl_price
        )
        if success:
            self._positions[position_id] = updated_pos
            self._producer.send(
                KAFKA_POSITIONS_LOGGER_TOPIC,
                CoreEvent[PositionEvent](
                    event_type=CoreEventType.POSITION_EVENT,
                    data=PositionEvent(
                        type="update",
                        user_id=self._user_id,
                        version_id=self._version_id,
                        position=pos,
                    ),
                )
                .model_dump_json()
                .encode(),
            )
        return success

    def close_position(
        self, position_id: str, amount: Decimal, price: float | None = None
    ) -> bool:
        """
        Closes a portion or all of an open position.
        The 'price' parameter is ignored as MT5 closes positions at the current market price.
        """
        pos = self._positions.get(position_id)
        if not pos:
            logger.error(f"Position with ID {position_id} not found for closing.")
            return False

        if pos.status == PositionStatus.PENDING:
            logger.error(
                f"Cannot close position {position_id} as it is a pending order. Use cancel_position instead."
            )
            return False

        success, _ = self._exchange.close_position(pos, amount)

        if success:
            if amount == pos.starting_amount:
                self._positions.pop(position_id, None)
            self._sync_positions()  # Resync state from terminal

        return success

    def close_all_positions(self) -> None:
        """
        Closes all open positions on the account.
        """
        self._exchange.close_all_positions()
        self._sync_positions()

    def cancel_position(self, position_id: str) -> bool:
        pos = self._positions.get(position_id)
        if not pos:
            logger.warning(
                f"Order {position_id} not in local cache. Attempting cancellation anyway."
            )
        elif pos.status != PositionStatus.PENDING:
            logger.error(
                f"Cannot cancel position {position_id} as it is not a pending order."
            )
            return False

        success = self._exchange.cancel_position(position_id)
        if success:
            self._positions.pop(position_id, None)
        return success

    def cancel_all_positions(self) -> None:
        self._exchange.cancel_all_positions()
        self._sync_positions()

    def _update_account_info(self) -> None:
        """Fetches the latest account information from the MT5 terminal."""
        self._account_info = mt5.account_info()
        if self._account_info is None:
            logger.error(f"Failed to get account info: {mt5.last_error()}")

    def _sync_positions(self) -> None:
        """
        Synchronizes the local position cache with the state from the MT5 terminal,
        including both open positions and pending orders.
        """
        logger.debug("Syncing positions with MT5 Terminal.")
        self._positions.clear()

        open_positions = mt5.positions_get()
        if open_positions:
            for pos in open_positions:
                position = self._mt5_pos_to_position(pos)
                self._positions[position.position_id] = position

        pending_orders = mt5.orders_get()
        if pending_orders:
            for order in pending_orders:
                position = self._mt5_order_to_position(order)
                self._positions[position.position_id] = position

    @staticmethod
    def _mt5_pos_to_position(mt5_pos) -> Position:
        side = Side.BID if mt5_pos.type == mt5.ORDER_TYPE_BUY else Side.ASK
        return Position(
            position_id=str(mt5_pos.ticket),
            instrument=mt5_pos.symbol,
            side=side,
            order_type=OrderType.MARKET,
            starting_amount=Decimal(str(mt5_pos.volume)),
            price=mt5_pos.price_open,
            tp_price=mt5_pos.tp or None,
            sl_price=mt5_pos.sl or None,
            status=PositionStatus.OPEN,
            limit_price=None,
            stop_price=None,
        )

    @staticmethod
    def _mt5_order_to_position(mt5_order) -> Position:
        order_type_map = {
            mt5.ORDER_TYPE_BUY_LIMIT: (OrderType.LIMIT, Side.BID),
            mt5.ORDER_TYPE_SELL_LIMIT: (OrderType.LIMIT, Side.ASK),
            mt5.ORDER_TYPE_BUY_STOP: (OrderType.STOP, Side.BID),
            mt5.ORDER_TYPE_SELL_STOP: (OrderType.STOP, Side.ASK),
            mt5.ORDER_TYPE_BUY_STOP_LIMIT: (OrderType.STOP_LIMIT, Side.BID),
            mt5.ORDER_TYPE_SELL_STOP_LIMIT: (OrderType.STOP_LIMIT, Side.ASK),
        }
        order_type, side = order_type_map.get(
            mt5_order.type, (OrderType.MARKET, Side.BID)
        )

        return Position(
            position_id=str(mt5_order.ticket),
            instrument=mt5_order.symbol,
            side=side,
            order_type=order_type,
            starting_amount=Decimal(str(mt5_order.volume_initial)),
            price=None,
            limit_price=mt5_order.price_open if order_type == OrderType.LIMIT else None,
            stop_price=mt5_order.price_open if order_type == OrderType.STOP else None,
            tp_price=mt5_order.tp or None,
            sl_price=mt5_order.sl or None,
            status=PositionStatus.PENDING,
        )

    @property
    def balance(self) -> Decimal:
        self._update_account_info()
        return (
            Decimal(str(self._account_info.balance))
            if self._account_info
            else Decimal("0.0")
        )

    @property
    def equity(self) -> Decimal:
        self._update_account_info()
        return (
            Decimal(str(self._account_info.equity))
            if self._account_info
            else Decimal("0.0")
        )

    @property
    def margin(self) -> Decimal:
        self._update_account_info()
        return (
            Decimal(str(self._account_info.margin))
            if self._account_info
            else Decimal("0.0")
        )

    @property
    def free_margin(self) -> Decimal:
        self._update_account_info()
        return (
            Decimal(str(self._account_info.margin_free))
            if self._account_info
            else Decimal("0.0")
        )
