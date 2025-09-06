from datetime import datetime
from uuid import UUID

from pydantic import field_validator

from core.enums import TaskStatus
from core.typing import CustomBaseModel


class BacktestResults(CustomBaseModel):
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
        return round(v, 2)


class StrategyCreate(CustomBaseModel):
    prompt: str
    name: str | None = None
    strategy_id: UUID | None = None


class StrategyCreateResponse(CustomBaseModel):
    strategy_id: UUID
    version_id: UUID


class StrategyVersionResponse(CustomBaseModel):
    version_id: UUID
    strategy_id: UUID
    name: str
    prompt: str
    backtest_status: TaskStatus
    created_at: datetime


class StrategiesResponse(CustomBaseModel):
    strategy_id: UUID
    name: str
    created_at: datetime


class StrategyVersionsResponse(CustomBaseModel):
    version_id: UUID
    name: str
    created_at: datetime
    backtest: BacktestResults


class BacktestRequest(CustomBaseModel):
    instrument: str = "EURUSD"
    starting_balance: float = 100_000
    leverage: int = 10


class BacktestCreateResponse(CustomBaseModel):
    backtest_id: UUID
    status: TaskStatus


class BacktestResultResponse(BacktestResults):
    backtest_id: UUID
    version_id: UUID
