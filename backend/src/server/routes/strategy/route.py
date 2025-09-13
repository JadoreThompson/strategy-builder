from datetime import timedelta
import json
from asyncio import TimeoutError as AIOTimeoutError
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    HTTPException,
    Request,
    WebSocket,
)
from fastapi.websockets import WebSocketState
from starlette.websockets import WebSocketDisconnect
from sqlalchemy import desc, insert, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import TaskStatus
from db_models import (
    BacktestPositions,
    Positions,
    Strategies,
    StrategyVersions,
    Backtests,
)
from server import tasks
from server.dependencies import depends_db_sess, depends_jwt
from server.exc import JWTError
from server.services import JWTService
from server.typing import JWTPayload
from .connection_manager import ConnectionManager
from .models import (
    BacktestCreate,
    BacktestCreateResponse,
    BacktestPositionsChartResponse,
    BacktestResult,
    BacktestResultResponse,
    Position,
    StrategiesResponse,
    StrategyCreate,
    StrategyCreateResponse,
    StrategyVersionResponse,
    StrategyVersionsResponse,
)


route = APIRouter(prefix="/strategies", tags=["strategies"])
conn_manager = ConnectionManager()


# ---- STRATEGIES ----
@route.post("/", response_model=StrategyCreateResponse)
async def create_strategy_version(
    body: StrategyCreate,
    background_tasks: BackgroundTasks,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
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
        .values(strategy_id=strategy_id, name=name, prompt=body.prompt)
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


# ---- STRATEGY VERSIONS ----
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

    backtest_ranked = select(
        Backtests,
        func.row_number()
        .over(partition_by=Backtests.version_id, order_by=Backtests.created_at.desc())
        .label("rn"),
    ).subquery()

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
            backtest_ranked.c.version_id == StrategyVersions.version_id,
            isouter=True,
        )
        .where(StrategyVersions.strategy_id == strategy_id, backtest_ranked.c.rn == 1)
    )

    if name:
        q = q.where(StrategyVersions.name == name)

    res = await db_sess.execute(q)
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

    return out


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


@route.delete("/versions/{version_id}")
async def delete_version(
    version_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    version = await db_sess.scalar(
        select(StrategyVersions)
        .join(Strategies, Strategies.strategy_id == StrategyVersions.strategy_id)
        .where(StrategyVersions.version_id == version_id, Strategies.user_id == jwt.sub)
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    await db_sess.delete(version)
    await db_sess.commit()

    return {"message": "Successfully deleted version"}


# ---- BACKTESTS ----
@route.post("/versions/{version_id}/backtest", response_model=BacktestCreateResponse)
async def create_backtest(
    version_id: UUID,
    body: BacktestCreate,
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

    bt_params = body.model_dump()
    bt_params["backtest_id"] = str(bt_dict["backtest_id"])
    background_tasks.add_task(tasks.run_backtest, bt_dict["backtest_id"], bt_params)

    return bt_dict


@route.get("/versions/{version_id}/backtests", response_model=list[BacktestResult])
async def get_backtests(
    version_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    owned_versions = (
        select(StrategyVersions.version_id)
        .join(Strategies, StrategyVersions.strategy_id == Strategies.strategy_id)
        .where(Strategies.user_id == jwt.sub)
    )

    res = await db_sess.scalars(
        select(Backtests).where(
            Backtests.version_id == version_id, Backtests.version_id.in_(owned_versions)
        )
    )

    return [
        BacktestResult(
            backtest_id=bt.backtest_id,
            status=bt.status,
            total_pnl=bt.total_pnl,
            starting_balance=bt.starting_balance,
            end_balance=bt.end_balance,
            total_trades=bt.total_trades,
            win_rate=bt.win_rate,
            created_at=bt.created_at,
        )
        for bt in res.all()
    ]


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


@route.get(
    "/backtests/{backtest_id}/positions-chart",
    response_model=list[BacktestPositionsChartResponse],
)
async def get_backtest_positions_chart(
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

    res = await db_sess.execute(
        select(BacktestPositions)
        .where(BacktestPositions.backtest_id == backtest_id)
        .order_by(BacktestPositions.created_at)
    )
    positions = res.scalars().all()
    if not positions:
        return []

    start_date, end_date = positions[0].closed_at, positions[-1].closed_at
    splits = 6
    interval: timedelta = (
        (end_date - start_date) / splits if end_date > start_date else timedelta(days=1)
    )

    chart: list[BacktestPositionsChartResponse] = [
        BacktestPositionsChartResponse(
            date=start_date.date(), balance=backtest.starting_balance, pnl=0.0
        )
    ]

    cur_balance = backtest.starting_balance
    cur_pnl = 0.0
    next_date = start_date + interval

    for pos in positions:
        if pos.closed_at is None:
            continue

        while pos.closed_at >= next_date:
            chart.append(
                BacktestPositionsChartResponse(
                    date=next_date.date(), balance=cur_balance, pnl=cur_pnl
                )
            )
            next_date += interval

        cur_balance += pos.realised_pnl
        cur_pnl += pos.realised_pnl

    # Add final point if missing
    if chart[-1].date < end_date.date():
        chart.append(
            BacktestPositionsChartResponse(
                date=end_date.date(), balance=cur_balance, pnl=cur_pnl
            )
        )

    return chart


# ---- POSITIONS ----
@route.get("/versions/{version_id}/positions", response_model=list[Position])
async def get_positions(
    version_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    res = await db_sess.scalars(
        select(Positions)
        .join(StrategyVersions, StrategyVersions.version_id == version_id)
        .join(Strategies, Strategies.strategy_id == StrategyVersions.strategy_id)
        .where(Positions.version_id == version_id, Positions.user_id == jwt.sub)
    )

    return [
        Position(
            id=p.position_id,
            instrument=p.instrument,
            side=p.side,
            order_type=p.order_type,
            starting_amount=p.starting_amount,
            current_amount=p.current_amount,
            price=p.price,
            limit_price=p.limit_price,
            stop_price=p.stop_price,
            tp_price=p.tp_price,
            sl_price=p.sl_price,
            realised_pnl=p.realised_pnl,
            unrealised_pnl=p.unrealised_pnl,
            status=p.status,
            created_at=p.created_at,
            close_price=p.close_price,
            closed_at=p.closed_at,
        )
        for p in res.all()
    ]


@route.websocket("/versions/{version_id}/positions")
async def positions_websocket(version_id: UUID, ws: WebSocket):  # , x = Depends(dep)):
    global conn_manager

    await ws.accept()

    try:
        m = await ws.receive_text()
        token = json.loads(m).get("token")
        payload = JWTService.decode(token)
    except AIOTimeoutError:
        await ws.close(reason="Token not received in time.")
    except (AttributeError, TypeError):
        await ws.close(reason="Invalid token.")
    except JWTError as e:
        await ws.close(reason=f"Invalid token {str(e)}.")

    user_id = payload.sub
    await conn_manager.connect(user_id, version_id, ws)

    try:
        while True:
            await ws.receive_bytes()
    except (RuntimeError, WebSocketDisconnect):
        pass
    finally:
        conn_manager.disconnect(user_id, version_id)
        if ws.state != WebSocketState.DISCONNECTED:
            await ws.close()
