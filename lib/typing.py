from collections import namedtuple
from typing import Literal


BullishBearish = Literal["bullish", "bearish"]


Tick = namedtuple("Tick", ("last", "bid", "ask", 'time'))
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
