from uuid import UUID
from datetime import datetime
from core.typing import CustomBaseModel
from core.enums import TaskStatus


class DeploymentCreate(CustomBaseModel):
    account_id: UUID
    version_id: UUID


class DeploymentResponse(CustomBaseModel):
    deployment_id: UUID
    account_id: UUID
    version_id: UUID
    status: TaskStatus
    created_at: datetime
