from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import TaskStatus
from db_models import BacktestPositions, Backtests, Strategies, StrategyVersions, Ticks
from server.dependencies import depends_db_sess, depends_jwt
from server.typing import JWTPayload
from .models import BacktestPositionsChartResponse, BacktestResultResponse


route = APIRouter(prefix="/backtests", tags=["backtests"])


@route.get("/{backtest_id}", response_model=BacktestResultResponse)
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
    "/{backtest_id}/positions-chart",
    response_model=list[BacktestPositionsChartResponse],
)
async def get_backtest_positions_chart(
    backtest_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    # NOTE: The final pnl shown is inequal to the final pnl
    # reported for the backtest. Assumed to be a rounding error
    # from Decimal to float, store position realised and unrealised pnls
    # as strings and convert to Decimal for processing.
    query = (
        select(Backtests)
        .join(StrategyVersions)
        .join(Strategies)
        .where(Backtests.backtest_id == backtest_id, Strategies.user_id == jwt.sub)
    )
    backtest = (await db_sess.execute(query)).scalar_one_or_none()
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found.")
    if backtest.status != TaskStatus.COMPLETED.value:
        raise HTTPException(status_code=404, detail="Backtest not complete.")

    first_tick = (
        select(Ticks.time)
        .where(Ticks.instrument == backtest.instrument.upper())
        .order_by(Ticks.time)
        .limit(1)
        .subquery()
    )

    last_tick = (
        select(Ticks.time)
        .where(Ticks.instrument == backtest.instrument.upper())
        .order_by(Ticks.time.desc())
        .limit(1)
        .subquery()
    )

    res = await db_sess.execute(
        select(
            first_tick.c.time.label("start_date"), last_tick.c.time.label("end_date")
        )
    )

    data = res.first()
    start_date, end_date = datetime.fromtimestamp(data[0], UTC), datetime.fromtimestamp(
        data[1], UTC
    )

    res = await db_sess.execute(
        select(BacktestPositions)
        .where(
            BacktestPositions.backtest_id == backtest_id,
            BacktestPositions.closed_at != None,
        )
        .order_by(BacktestPositions.created_at)
    )
    positions = res.scalars().all()
    if not positions:
        return []

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
