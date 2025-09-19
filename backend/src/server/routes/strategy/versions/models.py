from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel

from core.enums import TaskStatus
from core.typing import CustomBaseModel


class BacktestCreate(CustomBaseModel):
    instrument: str = "EURUSD"
    starting_balance: float = 100_000
    leverage: int = 10


class BacktestCreateResponse(CustomBaseModel):
    backtest_id: UUID
    status: TaskStatus


class BacktestPositionsChartResponse(BaseModel):
    date: date
    balance: float
    pnl: float


class PositionResponse(CustomBaseModel):
    position_id: str
    instrument: str
    side: str
    order_type: str
    starting_amount: float
    current_amount: float | None
    price: float | None
    limit_price: float | None
    stop_price: float | None
    tp_price: float | None
    sl_price: float | None
    realised_pnl: float | None
    unrealised_pnl: float | None
    status: str
    created_at: datetime | None
    close_price: float | None
    closed_at: datetime | None
