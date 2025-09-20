from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import DeploymentStatus
from db_models import Deployments, Accounts
from server.dependencies import depends_db_sess, depends_jwt
from server.models import DeploymentResponse
from server.typing import JWTPayload


route = APIRouter(prefix="/deployments", tags=["deployments"])


@route.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    res = await db_sess.execute(
        select(Deployments, Accounts.name)
        .join(Accounts)
        .where(Deployments.deployment_id == deployment_id, Accounts.user_id == jwt.sub)
    )
    data = res.first()
    if not data or len(data) != 2:
        raise HTTPException(status_code=404, detail="Deployment not found")

    deployment, name = data
    return DeploymentResponse(
        deployment_id=deployment.deployment_id,
        account_id=deployment.account_id,
        account_name=name,
        version_id=deployment.version_id,
        status=deployment.status,
        created_at=deployment.created_at,
    )


@route.post("/{deployment_id}/stop")
async def stop_deployment(
    deployment_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    deployment = await db_sess.scalar(
        select(Deployments)
        .join(Accounts)
        .where(Deployments.deployment_id == deployment_id, Accounts.user_id == jwt.sub)
    )
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    if deployment.status not in (
        DeploymentStatus.PENDING,
        DeploymentStatus.STOPPED,
        DeploymentStatus.FAILED,
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Deployment in status '{deployment.status}' cannot be stopped.",
        )

    await db_sess.execute(
        update(Deployments)
        .where(Deployments.deployment_id == deployment_id)
        .values(status=DeploymentStatus.STOPPED.value)
    )
    await db_sess.commit()
    return {"message": "Deployment stopped successfully."}
