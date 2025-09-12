import logging
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from core.enums import TaskStatus
from db_models import StrategyVersions, Backtests
from server.services import BacktestService, LLMService
from utils import get_db_sess, get_db_sess_sync


logger = logging.getLogger(__name__)


async def generate_strategy_code(version_id: UUID, prompt: str):
    logger.info(f"Starting strategy generation for version_id: {version_id}")
    try:
        success, txt = await LLMService.generate_code(prompt)
        if not success:
            raise Exception(txt)

        cleaned_code = LLMService.clean_code(txt)

        async with get_db_sess() as db_sess:
            await db_sess.execute(
                update(StrategyVersions)
                .where(StrategyVersions.version_id == version_id)
                .values(code=cleaned_code, status=TaskStatus.COMPLETED.value)
            )
            await db_sess.commit()
        logger.info(f"Successfully generated strategy for version_id: {version_id}")
    except Exception as e:
        logger.error(
            f"Failed to generate strategy for version_id: {version_id}. Error: {e}"
        )
        async with get_db_sess() as db_sess:
            await db_sess.execute(
                update(StrategyVersions)
                .where(StrategyVersions.version_id == version_id)
                .values(status=TaskStatus.FAILED.value)
            )
            await db_sess.commit()


def run_backtest(backtest_id: UUID, backtest_params: dict):
    logger.info(f"Starting backtest for backtest_id: {backtest_id}")

    try:
        with get_db_sess_sync() as db_sess:
            backtest_run = db_sess.scalar(
                select(Backtests)
                .options(selectinload(Backtests.strategy_version))
                .where(Backtests.backtest_id == backtest_id)
            )
            if not backtest_run or not backtest_run.strategy_version.code:
                raise Exception("Backtest record or strategy code not found.")

            strategy_code = backtest_run.strategy_version.code

        bt_service = BacktestService()
        results = bt_service.run(strategy_code, backtest_params)

        with get_db_sess_sync() as db_sess:
            db_sess.execute(
                update(Backtests)
                .where(Backtests.backtest_id == backtest_id)
                .values(**results, status=TaskStatus.COMPLETED.value)
            )
            db_sess.commit()

        logger.info(f"Successfully completed backtest for backtest_id: {backtest_id}")
    except Exception as e:
        logger.error(
            f"Failed to run backtest for backtest_id: {backtest_id}. Error: {e}"
        )
        with get_db_sess_sync() as db_sess:
            db_sess.execute(
                update(Backtests)
                .where(Backtests.backtest_id == backtest_id)
                .values(status=TaskStatus.FAILED.value)
            )
            db_sess.commit()
