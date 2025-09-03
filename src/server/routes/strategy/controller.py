from sqlalchemy import select
from db_models import Strategies, StrategyVersions
from sqlalchemy.ext.asyncio import AsyncSession

from server.routes.strategy.models import StrategyCreate


async def create_strategy(strategy: StrategyCreate, db_sess: AsyncSession): ...


async def update_strategy(strategy: StrategyCreate, db_sess: AsyncSession): ...


def backtest_strategy(): ...


async def update_strategy(): ...
