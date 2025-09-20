import logging
import os

from sqlalchemy import select, update

from config import BASE_PATH, RESOURCES_PATH
from core.enums import DeploymentStatus
from core.events import DeploymentEvent
from db_models import Accounts, Deployments, StrategyVersions
from utils import get_db_sess_sync


logger = logging.getLogger(__name__)


class DeploymentConsumer:
    """
    Consumes deployment event and handles the deployment
    of a strategy.
    """
    def __init__(self):
        pass

    def consume(self, event: DeploymentEvent) -> None:
        with get_db_sess_sync() as db_sess:
            res = db_sess.execute(
                select(
                    Deployments.instrument,
                    Deployments.version_id,
                    Accounts.platform,
                    Accounts.login,
                    Accounts.password,
                    Accounts.server,
                    Accounts.user_id,
                    StrategyVersions.code,
                )
                .join(Accounts, Accounts.account_id == Deployments.account_id)
                .join(
                    StrategyVersions,
                    StrategyVersions.version_id == Deployments.version_id,
                )
                .where(Deployments.deployment_id == event.deployment_id)
            )
            db_data = res.first()

        if not db_data:
            logger.info(
                f"Deployment data not found for id {event.deployment_id}. Abandoning deployment."
            )
            return

        mainpy = open(os.path.join(RESOURCES_PATH, "deployment.txt"), "r").read()
        mainpy = mainpy.format(
            strategy_code=db_data.code,
            version_id=db_data.version_id,
            deployment_id=event.deployment_id,
            instrument=db_data.instrument,
            parent_folder=BASE_PATH,
            creds={
                "login": db_data.login,
                "password": db_data.password,
                "server": db_data.server,
            },
            user_id=db_data.user_id,
        )

        try:
            code = compile(mainpy, "<string>", "exec")
            res = exec(code, {})
        except Exception as e:
            with get_db_sess_sync() as db_sess:
                db_sess.execute(
                    update(Deployments)
                    .values(status=DeploymentStatus.FAILED.value, reason=str(e))
                    .where(Deployments.deployment_id == event.deployment_id)
                )
                db_sess.commit()

            logger.error(f"Error performing deployment: {type(e)} - {str(e)}")
