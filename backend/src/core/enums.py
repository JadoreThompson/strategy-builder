from enum import Enum


class StrategyType(Enum):
    FUTURES = 0
    SPOT = 1


class Side(Enum):
    ASK = 0
    BID = 1


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class PositionStatus(Enum):
    PENDING = 0
    OPEN = 1
    CLOSED = 2
    CANCELLED = 3


class TaskStatus(str, Enum):
    NOT_STARTED = 'not_started'
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    

class DeploymentStatus(str, Enum):
    NOT_DEPLOYED  = 'not_deployed'
    DEPLOYED = 'deployed'
    FAILED = 'failed'