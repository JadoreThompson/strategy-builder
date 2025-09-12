from uuid import UUID
from datetime import datetime

from core.enums import DeploymentStatus
from core.typing import CustomBaseModel


class DeploymentCreate(CustomBaseModel):
    account_id: UUID
    version_id: UUID


class DeploymentResponse(CustomBaseModel):
    deployment_id: UUID
    account_id: UUID
    account_name: str
    version_id: UUID
    status: DeploymentStatus
    created_at: datetime
