from datetime import datetime
from typing import Union
from uuid import UUID

from pydantic import field_validator

from core.enums import TaskStatus, DeploymentStatus
from core.typing import CustomBaseModel


# ---- STRATEGIES ----
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


# ---- STRATEGY VERSIONS ----
class StrategyVersionResponse(CustomBaseModel):
    version_id: UUID
    strategy_id: UUID
    name: str
    prompt: str
    backtest_status: TaskStatus
    deployment_status: DeploymentStatus
    created_at: datetime


class StrategyVersionsResponse(CustomBaseModel):
    version_id: UUID
    name: str
    created_at: datetime
    deployment_status: DeploymentStatus
    backtest: Union["BacktestResult", None]


# ---- BACKTESTS ----
class BacktestCreate(CustomBaseModel):
    instrument: str = "EURUSD"
    starting_balance: float = 100_000
    leverage: int = 10


class BacktestCreateResponse(CustomBaseModel):
    backtest_id: UUID
    status: TaskStatus


class BacktestResult(CustomBaseModel):
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


# ---- POSITIONS ----
class Position(CustomBaseModel):
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
