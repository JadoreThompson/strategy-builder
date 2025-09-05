import logging
from decimal import Decimal
from typing import Generator
from uuid import uuid4

import pandas as pd

from core.enums import OrderType, PositionStatus, Side
from lib.typing import MODIFY_SENTINEL, Position, Tick
from .futures_exchange import FuturesExchange


logger = logging.getLogger(__name__)

SENTINEL_POSITION = (
    Position(
        id="tmp",
        instrument="tmp-instrument",
        side=Side.ASK,
        order_type=OrderType.MARKET,
        starting_amount=Decimal("10"),
        price=100.0,
        status=PositionStatus.OPEN,
    ),
)


class BacktestFuturesExchange(FuturesExchange):

    def __init__(
        self,
        login_creds: dict,
        df_path: str | None = None,
        df: pd.DataFrame | None = None,
    ):
        super().__init__(login_creds)
        self._df_path = df_path
        self._df = df

    def login(self) -> bool:
        return True

    def subscribe(self, instrument: str) -> Generator[Tick, None, None]:
        """
        Subscribes to price stream and yields the ticks

        Args:
            instrument (str): Instrument to subscribe to

        Yields:
            Generator[Tick, None, None]: Tick object
        """
        if self._df_path:
            reader = pd.read_csv(self._df_path, chunksize=1000)
            for chunk in reader:
                for dt, row in chunk.iterrows():
                    self._last_tick = Tick(last=row["close"], time=dt)
                    yield self._last_tick
        else:
            for dt, row in self._df.iterrows():
                self._last_tick = Tick(last=row["close"], time=dt)
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
        if self._last_tick is None:
            return

        # Entry validation
        if order_type == OrderType.MARKET:
            open_price = self._last_tick.last

        elif order_type == OrderType.LIMIT:
            if limit_price is None:
                return

            if (side == Side.ASK and limit_price <= self._last_tick.last) or (
                side == Side.BID and limit_price >= self._last_tick.last
            ):
                return

            open_price = limit_price

        elif order_type == OrderType.STOP:
            if stop_price is None:
                return

            if (side == Side.ASK and stop_price >= self._last_tick.last) or (
                side == Side.BID and stop_price <= self._last_tick.last
            ):
                return

            open_price = stop_price

        if sl_price is not None:
            tmp_sl_price = sl_price
        else:
            tmp_sl_price = float("inf") if side == Side.ASK else float("-inf")

        if tp_price is not None:
            tmp_tp_price = tp_price
        else:
            tmp_tp_price = float("-inf") if side == Side.ASK else float("inf")

        if (side == Side.ASK and not tmp_sl_price > open_price > tmp_tp_price) or (
            side == Side.BID and not tmp_sl_price < open_price < tmp_tp_price
        ):
            return

        return Position(
            id=str(uuid4()),
            instrument=instrument,
            side=side,
            order_type=order_type,
            starting_amount=amount,
            price=self._last_tick.last if order_type == OrderType.MARKET else None,
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

    def modify_position(
        self,
        position: Position,
        limit_price: float | None = MODIFY_SENTINEL,
        stop_price: float | None = MODIFY_SENTINEL,
        tp_price: float | None = MODIFY_SENTINEL,
        sl_price: float | None = MODIFY_SENTINEL,
    ) -> tuple[bool, Position]:
        side = position.side
        ot = position.order_type

        if ot == OrderType.MARKET:
            tmp_oprice = position.price
        elif ot == OrderType.LIMIT:
            tmp_oprice = position.limit_price
        else:
            tmp_oprice = position.stop_price

        # Entry price validation
        if ot == OrderType.MARKET and (
            limit_price != MODIFY_SENTINEL or stop_price != MODIFY_SENTINEL
        ):
            return (False, position)
        elif ot == OrderType.LIMIT:
            if limit_price is None:
                return (False, position)

            if limit_price != MODIFY_SENTINEL:
                if (side == Side.ASK and limit_price <= self._last_tick.last) or (
                    side == Side.BID and limit_price >= self._last_tick.last
                ):
                    return (False, position)

                tmp_oprice = limit_price

        elif ot == OrderType.STOP:
            if stop_price is None:
                return (False, position)

            if stop_price != MODIFY_SENTINEL:
                if (side == Side.ASK and stop_price >= self._last_tick.last) or (
                    side == Side.BID and stop_price <= self._last_tick.last
                ):
                    return (False, position)

                tmp_oprice = stop_price

        # TP/SL Validation
        tmp_tp_price = position.tp_price
        tmp_sl_price = position.sl_price

        if tp_price != MODIFY_SENTINEL:
            if tp_price is None:
                tmp_tp_price = float("inf") if side == Side.BID else float("-inf")
            else:
                tmp_tp_price = tp_price

        if sl_price != MODIFY_SENTINEL:
            if sl_price is None:
                tmp_sl_price = float("-inf") if side == Side.BID else float("inf")
            else:
                tmp_sl_price = sl_price

        if (side == Side.BID and not tmp_sl_price < tmp_oprice < tmp_tp_price) or (
            side == Side.ASK and not tmp_sl_price > tmp_oprice > tmp_tp_price
        ):
            return (False, position)

        updated = Position(
            id=position.id,
            instrument=position.instrument,
            side=position.side,
            order_type=position.order_type,
            starting_amount=position.starting_amount,
            price=position.price,
            limit_price=(
                limit_price if limit_price != MODIFY_SENTINEL else position.limit_price
            ),
            stop_price=(
                stop_price if stop_price != MODIFY_SENTINEL else position.stop_price
            ),
            tp_price=tp_price if tp_price != MODIFY_SENTINEL else position.tp_price,
            sl_price=sl_price if sl_price != MODIFY_SENTINEL else position.sl_price,
        )
        return (True, updated)

    def close_position(
        self, position: Position, amount: Decimal
    ) -> tuple[bool, Position]:
        return (True, SENTINEL_POSITION)

    def close_all_positions(self) -> None:
        return

    def cancel_position(self, position_id: str) -> bool:
        return True

    def cancel_all_positions(self) -> None:
        return
