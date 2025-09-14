from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, field_validator

from core.enums import TaskStatus
from core.typing import CustomBaseModel


class BacktestResult(CustomBaseModel):
    backtest_id: UUID
    status: TaskStatus
    total_pnl: float | None
    starting_balance: float | None
    end_balance: float | None
    total_trades: int | None
    win_rate: float | None
    created_at: datetime

    @field_validator(
        "total_pnl", "starting_balance", "end_balance", "win_rate", mode="after"
    )
    def round_values(cls, v):
        if v is not None:
            return round(v, 2)


class BacktestResultResponse(BacktestResult):
    backtest_id: UUID
    version_id: UUID


class BacktestPositionsChartResponse(BaseModel):
    date: date
    balance: float
    pnl: float
