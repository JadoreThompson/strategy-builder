from datetime import datetime
from typing import Union
from uuid import UUID

from pydantic import field_validator

from core.enums import TaskStatus, DeploymentStatus
from core.typing import CustomBaseModel


class StrategyCreate(CustomBaseModel):
    prompt: str
    name: str | None = None
    strategy_id: UUID | None = None


class StrategyCreateResponse(CustomBaseModel):
    strategy_id: UUID
    version_id: UUID


class StrategiesResponse(CustomBaseModel):
    strategy_id: UUID
    name: str
    created_at: datetime


class StrategyVersionsResponse(CustomBaseModel):
    version_id: UUID
    name: str
    created_at: datetime
    deployment_status: DeploymentStatus
    backtest: Union["BacktestResult", None]


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
