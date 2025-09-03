from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal, NamedTuple

from core.enums import OrderType, PositionStatus, Side
from utils import get_datetime


BullishBearish = Literal["bullish", "bearish"]


class Tick(NamedTuple):
    last: Decimal
    time: datetime


class OHLC(NamedTuple):
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal


class FVG(NamedTuple):
    above: Decimal
    below: Decimal


class BullishBOS(NamedTuple):
    type: str
    present: bool
    first_low_idx: int
    high_idx: int
    second_low_idx: int
    breakout_idx: int


class BearishBOS(NamedTuple):
    type: str
    present: bool
    first_high_idx: int
    low_idx: int
    second_high_idx: int
    breakout_idx: int


# TODO: Add support for partials
@dataclass
class Position:
    id: str
    instrument: str
    side: Side
    order_type: OrderType
    starting_amount: Decimal
    current_amount: Decimal = None
    price: Decimal | None = None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    tp_price: Decimal | None = None
    sl_price: Decimal | None = None
    realised_pnl: Decimal | None = Decimal("0.0")
    unrealised_pnl: Decimal | None = Decimal("0.0")
    status: PositionStatus = PositionStatus.PENDING
    created_at: datetime | None = field(default_factory=get_datetime)
    close_price: Decimal | None = None
    closed_at: datetime | None = None

    def __post_init__(self):
        self.current_amount = self.starting_amount


@dataclass
class BacktestResult:
    total_pnl: Decimal
    starting_balance: Decimal
    end_balance: Decimal
    total_trades: int
    win_rate: float
