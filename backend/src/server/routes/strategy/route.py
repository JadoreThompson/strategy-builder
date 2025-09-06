from pprint import pprint
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
    BacktestResults,
    StrategiesResponse,
    StrategyCreate,
    StrategyCreateResponse,
    StrategyVersionResponse,
    BacktestRequest,
    BacktestCreateResponse,
    BacktestResultResponse,
    StrategyVersionsResponse,
)


route = APIRouter(prefix="/strategies", tags=["strategy"])


@route.post("/", response_model=StrategyCreateResponse)
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

    return StrategyCreateResponse(strategy_id=strategy_id, version_id=version_id)


@route.get("/", response_model=list[StrategiesResponse])
async def get_strategies(
    name: str | None = None,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    q = select(Strategies.strategy_id, Strategies.name, Strategies.created_at).where(
        Strategies.user_id == jwt.sub
    )

    if name:
        q = q.where(Strategies.name.like(f"%{name}%"))

    res = await db_sess.execute(q)
    data = res.all()
    return [
        StrategiesResponse(strategy_id=strat_id, name=name, created_at=created_at)
        for strat_id, name, created_at in data
    ]


@route.get("/{strategy_id}/versions", response_model=list[StrategyVersionsResponse])
async def get_strategy_versions(
    strategy_id: UUID,
    name: str | None = None,
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

    q = select(
        StrategyVersions.version_id,
        StrategyVersions.name,
        StrategyVersions.created_at,
        Backtests,
    ).where(StrategyVersions.strategy_id == strategy_id)

    if name:
        q = q.where(StrategyVersions.name.like(f"%{name}%"))

    q = q.join(
        Backtests, Backtests.version_id == StrategyVersions.version_id, isouter=True
    )

    res = await db_sess.execute(q)
    versions = res.all()

    return [
        StrategyVersionsResponse(
            version_id=vid,
            name=name,
            created_at=created_at,
            backtest=BacktestResults(
                status=bt.status,
                total_pnl=bt.total_pnl,
                starting_balance=bt.starting_balance,
                end_balance=bt.end_balance,
                total_trades=bt.total_trades,
                win_rate=bt.win_rate,
                created_at=bt.created_at,
            ),
        )
        for vid, name, created_at, bt in versions
    ]


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
