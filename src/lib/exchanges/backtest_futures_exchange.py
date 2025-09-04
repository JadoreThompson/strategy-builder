import logging
from decimal import Decimal
from typing import Generator
from uuid import uuid4

import pandas as pd

from core.enums import OrderType, PositionStatus, Side
from lib.typing import MODIFY_SENTINEL, Position, Tick
from .futures_exchange import FuturesExchange


logger = logging.getLogger(__name__)

SENITNEL_POSITION = (
    Position(
        id="tmp",
        instrument="tmp-instrument",
        side=Side.ASK,
        order_type=OrderType.MARKET,
        starting_amount=Decimal("10"),
        price=Decimal("100.0"),
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
        price: Decimal | None = None,
        limit_price: Decimal | None = None,
        stop_price: Decimal | None = None,
        tp_price: Decimal | None = None,
        sl_price: Decimal | None = None,
    ) -> Position | None:
        return Position(
            id=str(uuid4()),
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

    def modify_position(
        self,
        position: Position,
        limit_price: Decimal | None = MODIFY_SENTINEL,
        stop_price: Decimal | None = MODIFY_SENTINEL,
        tp_price: Decimal | None = MODIFY_SENTINEL,
        sl_price: Decimal | None = MODIFY_SENTINEL,
    ) -> tuple[bool, Position]:
        updated = Position(
            id=position.id,
            instrument=position.instrument,
            side=position.side,
            order_type=position.order_type,
            starting_amount=position.starting_amount,
            price=position.price,
            limit_price=(
                limit_price if limit_price is not None else position.limit_price
            ),
            stop_price=stop_price if stop_price is not None else position.stop_price,
            tp_price=tp_price if tp_price is not None else position.tp_price,
            sl_price=sl_price if sl_price is not None else position.sl_price,
        )
        return (True, updated)

    def close_position(
        self, position: Position, price: Decimal, amount: Decimal
    ) -> tuple[bool, Position]:
        return (True, SENITNEL_POSITION)

    def close_all_positions(self) -> None:
        return

    def cancel_position(self, position_id: str) -> bool:
        return True

    def cancel_all_positions(self) -> None:
        return
