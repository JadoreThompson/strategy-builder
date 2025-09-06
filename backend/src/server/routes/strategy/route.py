from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy import delete, insert, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.enums import TaskStatus
from db_models import Strategies, StrategyVersions, Backtests
from server import tasks
from server.dependencies import depends_db_sess, depends_jwt
from server.typing import JWTPayload
from .models import (
    StrategyCreate,
    StrategyResponse,
    StrategyVersionResponse,
    BacktestRequest,
    BacktestCreateResponse,
    BacktestResultResponse,
)


route = APIRouter(prefix="/strategies", tags=["strategy"])


@route.post("/", response_model=StrategyResponse)
async def create_strategy_version(
    body: StrategyCreate,
    background_tasks: BackgroundTasks,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    strategy_id = body.strategy_id
    user_id = jwt.sub

    if not strategy_id:
        if not body.name:
            raise HTTPException(
                status_code=400, detail="A name is required for new strategies."
            )

        new_strategy = await db_sess.scalar(
            insert(Strategies)
            .values(user_id=user_id, name=body.name)
            .returning(Strategies)
        )
        strategy_id = new_strategy.strategy_id
        version_count = 0
    else:
        strat_check = await db_sess.scalar(
            select(Strategies).where(
                Strategies.strategy_id == strategy_id, Strategies.user_id == user_id
            )
        )
        if not strat_check:
            raise HTTPException(status_code=404, detail="Strategy not found.")

        version_count = await db_sess.scalar(
            select(func.count())
            .select_from(StrategyVersions)
            .where(StrategyVersions.strategy_id == strategy_id)
        )

    res = await db_sess.execute(
        insert(StrategyVersions)
        .values(
            strategy_id=strategy_id, name=f"v{version_count + 1}", prompt=body.prompt
        )
        .returning(StrategyVersions.version_id)
    )
    version_id = res.scalar()

    await db_sess.commit()

    background_tasks.add_task(tasks.generate_strategy_code, version_id, body.prompt)

    return StrategyResponse(strategy_id=strategy_id, version_id=version_id)


@route.get("/{strategy_id}/versions")
async def get_strategy_versions(
    strategy_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    strategy = await db_sess.scalar(
        select(Strategies).where(
            Strategies.strategy_id == strategy_id, Strategies.user_id == jwt.sub
        )
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    version_ids = (
        await db_sess.scalars(
            select(StrategyVersions.version_id).where(
                StrategyVersions.strategy_id == strategy_id
            )
        )
    ).all()
    return version_ids


@route.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    strategy = await db_sess.scalar(
        select(Strategies).where(
            Strategies.strategy_id == strategy_id, Strategies.user_id == jwt.sub
        )
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    await db_sess.delete(strategy)
    await db_sess.commit()


@route.get("/versions/{version_id}", response_model=StrategyVersionResponse)
async def get_strategy_version(
    version_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    query = (
        select(StrategyVersions)
        .join(Strategies)
        .where(StrategyVersions.version_id == version_id, Strategies.user_id == jwt.sub)
    )
    version = (await db_sess.execute(query)).scalar_one_or_none()

    if not version:
        raise HTTPException(status_code=404, detail="Strategy version not found.")
    return version


@route.post("/versions/{version_id}/backtest", response_model=BacktestCreateResponse)
async def create_backtest(
    version_id: UUID,
    body: BacktestRequest,
    background_tasks: BackgroundTasks,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    version_check = await db_sess.scalar(
        select(StrategyVersions)
        .join(Strategies)
        .where(
            StrategyVersions.version_id == version_id,
            Strategies.user_id == jwt.sub,
            StrategyVersions.code != None,
        )
    )
    if not version_check or version_check.backtest_status == TaskStatus.PENDING.value:
        raise HTTPException(
            status_code=400, detail="Strategy version is not ready for backtesting."
        )

    res = await db_sess.execute(
        insert(Backtests).values(version_id=version_id).returning(Backtests)
    )
    backtest = res.scalar()
    bt_dict = backtest.__dict__.copy()
    bt_dict.pop("_sa_instance_state", None)
    await db_sess.commit()

    background_tasks.add_task(
        tasks.run_backtest, bt_dict["backtest_id"], body.model_dump()
    )

    return bt_dict


@route.get("/backtests/{backtest_id}", response_model=BacktestResultResponse)
async def get_backtest_result(
    backtest_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    query = (
        select(Backtests)
        .join(StrategyVersions)
        .join(Strategies)
        .where(Backtests.backtest_id == backtest_id, Strategies.user_id == jwt.sub)
    )
    backtest = (await db_sess.execute(query)).scalar_one_or_none()

    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found.")
    return backtest
