from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal, NamedTuple

from core.enums import OrderType, PositionStatus, Side
from utils import get_datetime


BullishBearish = Literal["bullish", "bearish"]


class Tick(NamedTuple):
    last: float
    time: datetime


class OHLC(NamedTuple):
    open: float
    high: float
    low: float
    close: float
    time: int


class FVG(NamedTuple):
    above: float
    below: float


class MSS(NamedTuple):
    type: BullishBearish
    present: bool
    swing_high_idx: int
    swing_low_idx: int
    breakout_idx: int


# TODO: Add support for partials
@dataclass
class Position:
    id: str | int
    instrument: str
    side: Side
    order_type: OrderType
    starting_amount: Decimal
    current_amount: Decimal = None
    price: float | None = None
    limit_price: float | None = None
    stop_price: float | None = None
    tp_price: float | None = None
    sl_price: float | None = None
    realised_pnl: Decimal | None = Decimal("0.0")
    unrealised_pnl: Decimal | None = Decimal("0.0")
    status: PositionStatus = PositionStatus.PENDING
    created_at: datetime | None = field(default_factory=get_datetime)
    close_price: float | None = None
    closed_at: datetime | None = None
    metadata: dict | None = None

    def __post_init__(self):
        self.current_amount = self.starting_amount


@dataclass
class BacktestResult:
    total_pnl: Decimal
    starting_balance: Decimal
    end_balance: Decimal
    total_trades: int
    win_rate: float


MODIFY_SENTINEL = "*"
