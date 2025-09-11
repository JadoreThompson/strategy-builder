import logging
from decimal import Decimal
from typing import Generator, TypedDict

import MetaTrader5 as mt5

from core.enums import OrderType, PositionStatus, Side
from lib.typing import MODIFY_SENTINEL, Position, Tick
from .futures_exchange import FuturesExchange


logger = logging.getLogger(__name__)


class CredsDict(TypedDict):
    login: int
    password: str
    server: str


class MT5FuturesExchange(FuturesExchange):
    """
    An implementation of the FuturesExchange for MetaTrader 5.
    """

    def __init__(self, login_creds: CredsDict):
        super().__init__(login_creds)
        self._is_logged_in = False

    def login(self) -> bool:
        """
        Initializes the connection to the MetaTrader 5 terminal.
        """
        if self._is_logged_in:
            return True

        if not mt5.initialize(
            login=self._login_creds.get("login"),
            server=self._login_creds.get("server"),
            password=self._login_creds.get("password"),
        ):
            logger.error(f"Failed to initialize MetaTrader 5: {mt5.last_error()}")
            return False

        self._is_logged_in = True
        logger.info("MetaTrader 5 initialized successfully.")
        return True

    def subscribe(self, instrument: str) -> Generator[Tick, None, None]:
        """
        Subscribes to the price stream for a given instrument.
        """
        if not self._is_logged_in:
            logger.error("Not logged into MetaTrader 5.")
            return

        symbol_info = mt5.symbol_info(instrument)
        if symbol_info is None:
            logger.error(f"Symbol {instrument} not found.")
            return

        if not mt5.symbol_select(instrument, True):
            logger.error(f"Failed to subscribe to {instrument}: {mt5.last_error()}")
            return

        while True:
            tick = mt5.symbol_info_tick(instrument)

            if tick:
                # Using midprice as last price
                self._last_tick = Tick(last=(tick.bid + tick.ask) / 2, time=tick.time)
                yield self._last_tick

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
    ) -> Position | None:
        """
        Opens a new position.
        """
        if not self._is_logged_in:
            logger.error("Not logged into MetaTrader 5.")
            return None

        trade_action = (
            mt5.TRADE_ACTION_DEAL
            if order_type == OrderType.MARKET
            else mt5.TRADE_ACTION_PENDING
        )
        mt5_order_type = self._map_order_type(order_type, side)

        price = 0.0
        if order_type == OrderType.MARKET:
            symbol_info_tick = mt5.symbol_info_tick(instrument)
            if not symbol_info_tick:
                logger.error(f"Could not retrieve tick for {instrument}")
                return None
            price = symbol_info_tick.ask if side == Side.BID else symbol_info_tick.bid
        
        elif order_type == OrderType.LIMIT:
            if limit_price is None:
                logger.error("Limit price must be set for a limit order.")
                return None
            price = limit_price
        
        elif order_type == OrderType.STOP:
            if stop_price is None:
                logger.error("Stop price must be set for a stop order.")
                return None
            price = stop_price

        request = {
            "action": trade_action,
            "symbol": instrument,
            "volume": float(amount),
            "type": mt5_order_type,
            "price": price,
            "sl": sl_price or 0.0,
            "tp": tp_price or 0.0,
            "magic": 234000,
            "comment": "python script open",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(request)
        if result is None:
            logger.error(f"Order send failed: {mt5.last_error()}")
            return None

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(
                f"Order failed: retcode={result.retcode}, comment={result.comment}"
            )
            return None

        return self._create_position_from_result(
            result, instrument, side, order_type, amount, price, sl_price, tp_price
        )

    def modify_position(
        self,
        position: Position,
        limit_price: float | None = MODIFY_SENTINEL,
        stop_price: float | None = MODIFY_SENTINEL,
        tp_price: float | None = MODIFY_SENTINEL,
        sl_price: float | None = MODIFY_SENTINEL,
    ) -> tuple[bool, Position]:
        """
        Modifies an existing open position or pending order.
        """
        if not self._is_logged_in:
            logger.error("Not logged into MetaTrader 5.")
            return False, position

        if position.id is None:
            logger.error("Position ID is not set.")
            return False, position

        request = {
            "action": mt5.TRADE_ACTION_MODIFY,
            "order": int(position.id),
            "sl": (
                sl_price
                if sl_price is not MODIFY_SENTINEL
                else position.sl_price or 0.0
            ),
            "tp": (
                tp_price
                if tp_price is not MODIFY_SENTINEL
                else position.tp_price or 0.0
            ),
        }
        if position.order_type == OrderType.LIMIT:
            request["price"] = (
                limit_price
                if limit_price is not MODIFY_SENTINEL
                else position.limit_price
            )
        elif position.order_type == OrderType.STOP:
            request["price"] = (
                stop_price if stop_price is not MODIFY_SENTINEL else position.stop_price
            )

        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            error_message = mt5.last_error() if result is None else result.comment
            logger.error(f"Failed to modify position {position.id}: {error_message}")
            return False, position

        updated_position = position.copy()
        if sl_price is not MODIFY_SENTINEL:
            updated_position.sl_price = sl_price
        if tp_price is not MODIFY_SENTINEL:
            updated_position.tp_price = tp_price
        if limit_price is not MODIFY_SENTINEL:
            updated_position.limit_price = limit_price
        if stop_price is not MODIFY_SENTINEL:
            updated_position.stop_price = stop_price

        return True, updated_position

    def close_position(
        self, position: Position, amount: Decimal, price: Decimal | None = None
    ) -> tuple[bool, Position]:
        """
        Closes a specified amount of an open position.
        """
        if not self._is_logged_in:
            logger.error("Not logged into MetaTrader 5.")
            return False, position

        if position.id is None:
            logger.error("Position ID is not set.")
            return False, position

        close_side = (
            mt5.ORDER_TYPE_SELL if position.side == Side.BID else mt5.ORDER_TYPE_BUY
        )

        close_price = price
        if not close_price:
            symbol_info_tick = mt5.symbol_info_tick(position.instrument)
            if not symbol_info_tick:
                logger.error(f"Could not retrieve tick for {position.instrument}")
                return False, position
            close_price = (
                symbol_info_tick.bid
                if position.side == Side.BID
                else symbol_info_tick.ask
            )

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": int(position.id),
            "symbol": position.instrument,
            "volume": float(amount),
            "type": close_side,
            "price": float(close_price),
            "magic": 234000,
            "comment": "python script close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            error_message = mt5.last_error() if result is None else result.comment
            logger.error(f"Failed to close position {position.id}: {error_message}")
            return False, position

        position.status = PositionStatus.CLOSED
        return True, position

    def close_all_positions(self) -> None:
        """
        Closes all open positions.
        """
        if not self._is_logged_in:
            logger.error("Not logged into MetaTrader 5.")
            return

        positions = mt5.positions_get()
        if positions is None:
            logger.error(f"Failed to get open positions: {mt5.last_error()}")
            return

        for pos in positions:
            self.close_position(
                Position(
                    id=str(pos.ticket),
                    instrument=pos.symbol,
                    side=Side.BID if pos.type == mt5.ORDER_TYPE_BUY else Side.ASK,
                    order_type=OrderType.MARKET,
                    starting_amount=Decimal(str(pos.volume)),
                    price=pos.price_open,
                    status=PositionStatus.OPEN,
                ),
                Decimal(str(pos.volume)),
            )

    def cancel_position(self, position_id: str) -> bool:
        """
        Cancels a pending order.
        """
        if not self._is_logged_in:
            logger.error("Not logged into MetaTrader 5.")
            return False

        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": int(position_id),
        }

        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            error_message = mt5.last_error() if result is None else result.comment
            logger.error(f"Failed to cancel order {position_id}: {error_message}")
            return False

        return True

    def cancel_all_positions(self) -> None:
        """
        Cancels all pending orders.
        """
        if not self._is_logged_in:
            logger.error("Not logged into MetaTrader 5.")
            return

        orders = mt5.orders_get()
        if orders is None:
            logger.error(f"Failed to get pending orders: {mt5.last_error()}")
            return

        for order in orders:
            self.cancel_position(str(order.ticket))

    def _map_order_type(self, order_type: OrderType, side: Side) -> int:
        if order_type == OrderType.MARKET:
            return mt5.ORDER_TYPE_BUY if side == Side.BID else mt5.ORDER_TYPE_SELL
        elif order_type == OrderType.LIMIT:
            return (
                mt5.ORDER_TYPE_BUY_LIMIT
                if side == Side.BID
                else mt5.ORDER_TYPE_SELL_LIMIT
            )
        elif order_type == OrderType.STOP:
            return (
                mt5.ORDER_TYPE_BUY_STOP
                if side == Side.BID
                else mt5.ORDER_TYPE_SELL_STOP
            )
        raise ValueError(f"Unsupported order type: {order_type}")

    def _create_position_from_result(
        self,
        result,
        instrument: str,
        side: Side,
        order_type: OrderType,
        amount: Decimal,
        price: float,
        sl_price: float | None,
        tp_price: float | None,
    ) -> Position:
        return Position(
            id=str(result.order),
            instrument=instrument,
            side=side,
            order_type=order_type,
            starting_amount=amount,
            price=price if order_type == OrderType.MARKET else None,
            limit_price=price if order_type == OrderType.LIMIT else None,
            stop_price=price if order_type == OrderType.STOP else None,
            sl_price=sl_price,
            tp_price=tp_price,
            status=(
                PositionStatus.OPEN
                if order_type == OrderType.MARKET
                else PositionStatus.PENDING
            ),
        )

    def __del__(self):
        """
        Shuts down the connection to the MetaTrader 5 terminal.
        """
        if self._is_logged_in:
            mt5.shutdown()
            logger.info("MetaTrader 5 connection shut down.")
