import json
from asyncio import TimeoutError as AIOTimeoutError
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    HTTPException,
    WebSocket,
)
from fastapi.websockets import WebSocketState
from starlette.websockets import WebSocketDisconnect
from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import TaskStatus
from db_models import Positions, Strategies, StrategyVersions, Backtests
from server import tasks
from server.dependencies import depends_db_sess, depends_jwt
from server.exc import JWTError
from server.models import StrategyVersionResponse, BacktestResult
from server.services import JWTService
from server.typing import JWTPayload
from .connection_manager import ConnectionManager
from .models import BacktestCreate, BacktestCreateResponse, Position


route = APIRouter(tags=["strategy-versions"])
conn_manager = ConnectionManager()


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
    if not version_check:
        raise HTTPException(status_code=404, detail="Strategy version not found")
    if version_check.backtest_status == TaskStatus.PENDING.value:
        raise HTTPException(
            status_code=400, detail="Strategy version is not ready for backtesting."
        )

    found = await db_sess.scalar(
        text("SELECT 1 FROM ticks where instrument = :instrument"),
        {"instrument": body.instrument},
    )
    if not found:
        raise HTTPException(
            status_code=400, detail=f"No backtest data available for {body.instrument}"
        )

    res = await db_sess.execute(
        insert(Backtests)
        .values(version_id=version_id, instrument=body.instrument)
        .returning(Backtests)
    )
    backtest = res.scalar()

    bt_dict = backtest.__dict__.copy()
    bt_dict.pop("_sa_instance_state", None)
    await db_sess.commit()

    bt_params = body.model_dump()
    bt_params["backtest_id"] = str(bt_dict["backtest_id"])
    background_tasks.add_task(tasks.run_backtest, bt_dict["backtest_id"], bt_params)

    return bt_dict


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
        select(Backtests)
        .where(
            Backtests.version_id == version_id, Backtests.version_id.in_(owned_versions)
        )
        .order_by(Backtests.created_at.desc())
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
        .order_by(Positions.created_at.desc())
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


@route.websocket("/versions/{version_id}/positions")
async def positions_websocket(
    version_id: UUID, ws: WebSocket, db_sess: AsyncSession = Depends(depends_db_sess)
):
    global conn_manager

    await ws.accept()

    try:
        m = await ws.receive_text()
        token = json.loads(m).get("token")
        payload = JWTService.decode(token)
    except AIOTimeoutError:
        await ws.close(code=1008, reason="Token not received in time.")
    except AttributeError:
        await ws.close(code=1008, reason="Invalid token.")
    except JWTError as e:
        await ws.close(code=1008, reason=f"Invalid token {str(e)}.")

    obj = await db_sess.scalar(
        select(1).select_from(
            select(Strategies)
            .join(
                StrategyVersions, StrategyVersions.strategy_id == Strategies.strategy_id
            )
            .where(
                StrategyVersions.version_id == version_id,
            )
        )
    )
    if not obj:
        await ws.close(code=1008, reason=f"Version not found.")

    user_id = payload.sub
    version_id = str(version_id)
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
