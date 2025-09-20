from typing import Generic, Literal, TypeVar
from uuid import UUID

from core.enums import CoreEventType
from core.typing import CustomBaseModel, Position


T = TypeVar("T")


class CoreEvent(CustomBaseModel, Generic[T]):
    event_type: CoreEventType
    data: T


class DeploymentEvent(CustomBaseModel):
    """
    Used to communicate a new deployment needs
    to be initiated.
    """

    deployment_id: UUID


class PositionEvent(CustomBaseModel):
    """
    Emited via the Strategy class, this object
    is used to log the position and then relay
    it to the corresponding websocket client.
    """

    type: Literal["new", "update"]
    user_id: str
    version_id: str
    position: Position
