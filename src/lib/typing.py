from collections import namedtuple
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from core.enums import OrderType, PositionStatus, Side
from utils import get_datetime


BullishBearish = Literal["bullish", "bearish"]


Tick = namedtuple("Tick", ("last", "time"))
OHLC = namedtuple("OHLC", ("open", "high", "low", "close", "time"))
FVG = namedtuple("FVG", ("above", "below"))
BullishBOS = namedtuple(
    "BullishBOS",
    ("type", "present", "first_low_idx", "high_idx", "second_low_idx", "breakout_idx"),
)
BearishBOS = namedtuple(
    "BearishBOS",
    ("type", "present", "first_high_idx", "low_idx", "second_high_idx", "breakout_idx"),
)


# TODO: Add support for partials
@dataclass
class Position:
    id: str
    instrument: str
    side: Side
    order_type: OrderType
    starting_amount: float
    current_amount: float = None
    price: float | None = None
    limit_price: float | None = None
    stop_price: float | None = None
    tp_price: float | None = None
    sl_price: float | None = None
    realised_pnl: float | None = 0.0
    unrealised_pnl: float | None = 0.0
    status: PositionStatus = PositionStatus.PENDING
    created_at: datetime | None = field(default_factory=get_datetime)
    close_price: float | None = None
    closed_at: datetime | None = None

    def __post_init__(self):
        self.current_amount = self.starting_amount


@dataclass
class BacktestResult:
    total_pnl: float
    starting_balance: float
    end_balance: float
    total_trades: int
    win_rate: float
