from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import insert, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from server.models import PaginatedResponse
from config import DEPLOYMENT_QUEUE, PAGE_SIZE
from core.typing import DeploymentPayload
from core.enums import DeploymentStatus, TaskStatus
from db_models import Deployments, Accounts, StrategyVersions
from server.dependencies import depends_db_sess, depends_jwt
from server.models import DeploymentResponse
from server.typing import JWTPayload
from .models import DeploymentCreate


route = APIRouter(prefix="/deployments", tags=["deployments"])


@route.post("/", response_model=DeploymentResponse)
async def create_deployment(
    body: DeploymentCreate,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    account = await db_sess.scalar(
        select(Accounts).where(
            Accounts.account_id == body.account_id, Accounts.user_id == jwt.sub
        )
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    variant = await db_sess.scalar(
        select(StrategyVersions).where(StrategyVersions.version_id == body.version_id)
    )
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    res = await db_sess.execute(
        insert(Deployments)
        .values(
            account_id=body.account_id,
            version_id=body.version_id,
            instrument=body.instrument,
            status=TaskStatus.PENDING.value,
        )
        .returning(Deployments)
    )
    deployment = res.scalar()

    dep_rsp = DeploymentResponse(
        deployment_id=deployment.deployment_id,
        account_id=deployment.account_id,
        account_name=account.name,
        version_id=deployment.version_id,
        instrument=deployment.instrument,
        status=deployment.status,
        created_at=deployment.created_at,
    )

    DEPLOYMENT_QUEUE.put_nowait(
        DeploymentPayload(deployment_id=deployment.deployment_id)
    )

    await db_sess.commit()

    return dep_rsp


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
