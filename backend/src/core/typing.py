from datetime import datetime
from enum import Enum
from json import loads
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal, NamedTuple

from core.enums import OrderType, PositionStatus, Side
from utils import get_datetime


class CustomBaseModel(BaseModel):
    model_config = {
        "json_encoders": {
            UUID: str,
            datetime: lambda dt: dt.isoformat(),
            Enum: lambda e: e.value,
        }
    }

    def to_serialisable_dict(self) -> dict:
        return loads(self.model_dump_json())


class DeploymentPayload(CustomBaseModel):
    deployment_id: UUID


# TODO: Add support for partials


class Position(CustomBaseModel):
    position_id: str # DB id
    instrument: str
    side: Side
    order_type: OrderType
    starting_amount: Decimal
    current_amount: Decimal = None
    price: float | None = None
    limit_price: float | None = None
    stop_price: float | None = None
    tp_price: float | None = None
    sl_price: float | None = None
    realised_pnl: Decimal | None = Decimal("0.0")
    unrealised_pnl: Decimal | None = Decimal("0.0")
    status: PositionStatus = PositionStatus.PENDING
    created_at: datetime | None = field(default_factory=get_datetime)
    close_price: float | None = None
    closed_at: datetime | None = None
    extras: dict | None = None # Extra platform specific data

    def __post_init_post_parse__(self):
        self.current_amount = self.starting_amount


class PositionMessage(CustomBaseModel):
    """Payload sent to the websocket connection manager"""

    topic: Literal["new", "update"]
    user_id: UUID
    version_id: UUID
    position: Position
