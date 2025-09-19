from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, field_validator

from core.enums import DeploymentStatus, TaskStatus
from core.typing import CustomBaseModel


T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    size: int
    has_next: bool


class PaginatedResponse(PaginationMeta, Generic[T]):
    data: list[T]


class StrategyVersionResponse(CustomBaseModel):
    version_id: UUID
    strategy_id: UUID
    name: str
    prompt: str
    backtest_status: TaskStatus
    deployment_status: DeploymentStatus
    created_at: datetime


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


class DeploymentResponse(CustomBaseModel):
    deployment_id: UUID
    account_id: UUID
    account_name: str
    instrument: str
    version_id: UUID
    status: DeploymentStatus
    created_at: datetime
