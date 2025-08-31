from enum import Enum


class Side(Enum):
    ASK = 0
    BID = 1


class OrderType(Enum):
    MARKET = 0
    LIMIT = 0
    STOP =0