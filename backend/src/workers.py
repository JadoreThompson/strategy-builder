import logging
import os
import time
from asyncio import Queue
from queue import Empty

import uvicorn
from sqlalchemy import select, update

from core.enums import DeploymentStatus
from config import BASE_PATH, RESOURCES_PATH
from core.typing import DeploymentPayload
from db_models import Accounts, Deployments, StrategyVersions
from utils import get_db_sess_sync


logger = logging.getLogger(__name__)


def run_server(queue) -> None:
    logger.info("Starting server.")
    import config

    config.DEPLOYMENT_QUEUE = queue
    uvicorn.run("server.app:app", port=80, host="localhost")


def _handle_deployment(payload: DeploymentPayload) -> None:
    # Temp solution

    with get_db_sess_sync() as db_sess:
        res = db_sess.execute(
            select(
                Deployments.instrument,
                Accounts.platform,
                Accounts.login,
                Accounts.password,
                Accounts.server,
                StrategyVersions.code,
            )
            .join(Accounts, Accounts.account_id == Deployments.account_id)
            .join(
                StrategyVersions, StrategyVersions.version_id == Deployments.version_id
            )
            .where(Deployments.deployment_id == payload.deployment_id)
        )
        data = res.first()

    if not data:
        logger.info(
            f"Deployment data not found for id {payload.deployment_id}. Abandoning deployment."
        )
        return

    mainpy = open(os.path.join(RESOURCES_PATH, "deployment.txt"), "r").read()
    mainpy = mainpy.format(
        strategy_code=data.code,
        deployment_id=payload.deployment_id,
        instrument=data.instrument,
        parent_folder=BASE_PATH,
        creds={"login": data.login, "password": data.password, "server": data.server},
    )

    print(mainpy)

    try:
        code = compile(mainpy, "<string>", "exec")
        res = exec(code, {})
    except Exception as e:
        with get_db_sess_sync() as db_sess:
            db_sess.execute(
                update(Deployments)
                .values(status=DeploymentStatus.FAILED.value, reason=str(e))
                .where(Deployments.deployment_id == payload.deployment_id)
            )
            db_sess.commit()

        print(type(e), str(e))


def deployment_queue_listener(queue: Queue) -> None:
    logger.info("Starting deployment queue listener.")
    started = False

    while True:
        try:
            if not started:
                started = True
                logger.info("Deployment queue listening.")

            data: DeploymentPayload = queue.get()
            _handle_deployment(data)
        except Empty:
            pass
        finally:
            time.sleep(1)
