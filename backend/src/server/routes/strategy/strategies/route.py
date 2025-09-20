from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import insert, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import PAGE_SIZE
from db_models import Strategies, StrategyVersions, Backtests
from server.dependencies import depends_db_sess, depends_jwt
from server.models import PaginatedResponse
from server.services import LLMService
from server.typing import JWTPayload
from .models import (
    BacktestResult,
    StrategiesResponse,
    StrategyCreate,
    StrategyCreateResponse,
    StrategyVersionsResponse,
)


route = APIRouter(prefix="/strategies", tags=["strategies"])


@route.post("/", response_model=StrategyCreateResponse)
async def create_strategy_version(
    body: StrategyCreate,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    success, txt = await LLMService.generate_code(body.prompt)
    if not success:
        raise HTTPException(txt)
    cleaned_code = LLMService.clean_code(txt)

    strategy_id = body.strategy_id
    user_id = jwt.sub
    name = body.name

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
        name = "v1"
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

        if not body.name:
            name = f"v{version_count + 1}"

    res = await db_sess.execute(
        insert(StrategyVersions)
        .values(
            strategy_id=strategy_id, name=name, prompt=body.prompt, code=cleaned_code
        )
        .returning(StrategyVersions.version_id)
    )
    version_id = res.scalar()

    await db_sess.commit()

    return StrategyCreateResponse(strategy_id=strategy_id, version_id=version_id)


@route.get("/", response_model=PaginatedResponse[StrategiesResponse])
async def get_strategies(
    name: str | None = None,
    page: int = 1,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    q = select(Strategies.strategy_id, Strategies.name, Strategies.created_at).where(
        Strategies.user_id == jwt.sub
    )

    if name:
        q = q.where(Strategies.name.like(f"%{name}%"))

    res = await db_sess.execute(
        q.order_by(Strategies.created_at.desc())
        .offset((page - 1) * 10)
        .limit(PAGE_SIZE + 1)
    )
    data = res.all()

    return PaginatedResponse[StrategiesResponse](
        page=page,
        size=min(PAGE_SIZE, len(data)),
        has_next=len(data) > PAGE_SIZE,
        data=[
            StrategiesResponse(strategy_id=strat_id, name=name, created_at=created_at)
            for strat_id, name, created_at in data
        ],
    )


@route.get(
    "/{strategy_id}/versions",
    response_model=PaginatedResponse[StrategyVersionsResponse],
)
async def get_strategy_versions(
    strategy_id: UUID,
    name: str | None = None,
    page: int = Query(1, ge=1),
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

    backtest_ranked_rn = select(
        Backtests,
        func.row_number()
        .over(partition_by=Backtests.version_id, order_by=Backtests.created_at.desc())
        .label("rn"),
    ).subquery()

    backtest_ranked = (
        select(backtest_ranked_rn).where(backtest_ranked_rn.c.rn == 1).subquery()
    )

    q = (
        select(
            StrategyVersions.version_id,
            StrategyVersions.name,
            StrategyVersions.deployment_status,
            StrategyVersions.created_at,
            backtest_ranked.c.backtest_id,
            backtest_ranked.c.status,
            backtest_ranked.c.total_pnl,
            backtest_ranked.c.starting_balance,
            backtest_ranked.c.end_balance,
            backtest_ranked.c.total_trades,
            backtest_ranked.c.win_rate,
            backtest_ranked.c.created_at.label("backtest_created_at"),
        )
        .join(
            backtest_ranked,
            StrategyVersions.version_id == backtest_ranked.c.version_id,
            isouter=True,
        )
        .where(StrategyVersions.strategy_id == strategy_id)
        .order_by(StrategyVersions.created_at.desc())
    )

    if name:
        q = q.where(StrategyVersions.name == name)

    # NOTE: MV may be better for pagination
    res = await db_sess.execute(q.offset((page - 1) * 10).limit(PAGE_SIZE + 1))
    rows = res.all()

    out = []
    for (
        vid,
        name,
        ds,
        created_at,
        backtest_id,
        bt_status,
        total_pnl,
        starting_balance,
        end_balance,
        total_trades,
        win_rate,
        backtest_created_at,
    ) in rows:
        backtest = None
        if backtest_id:
            backtest = BacktestResult(
                backtest_id=backtest_id,
                status=bt_status,
                total_pnl=total_pnl,
                starting_balance=starting_balance,
                end_balance=end_balance,
                total_trades=total_trades,
                win_rate=win_rate,
                created_at=backtest_created_at,
            )

        sv = StrategyVersionsResponse(
            version_id=vid,
            name=name,
            created_at=created_at,
            deployment_status=ds,
            backtest=backtest,
        )

        out.append(sv)

    return PaginatedResponse[StrategyVersionsResponse](
        page=page,
        size=min(PAGE_SIZE, len(out)),
        has_next=len(out) > PAGE_SIZE,
        data=out[:PAGE_SIZE],
    )


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
    return {"message": "Successfully deleted  strategy"}
