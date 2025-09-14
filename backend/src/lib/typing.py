from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal, NamedTuple
from uuid import UUID

from core.enums import OrderType, PositionStatus, Side
from core.typing import CustomBaseModel, Position
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


class BacktestResult(CustomBaseModel):
    backtest_id: str
    total_pnl: Decimal
    starting_balance: Decimal
    end_balance: Decimal
    total_trades: int
    win_rate: float
    positions: list[Position]


MODIFY_SENTINEL = "*"
