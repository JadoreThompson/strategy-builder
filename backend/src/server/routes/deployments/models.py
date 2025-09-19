from uuid import UUID
from datetime import datetime

from core.enums import DeploymentStatus
from core.typing import CustomBaseModel


class DeploymentCreate(CustomBaseModel):
    account_id: UUID
    version_id: UUID
    instrument: str
