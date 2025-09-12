import logging
from multiprocessing import Process
import os
import subprocess
import time
from asyncio import Queue
from tempfile import TemporaryDirectory
from queue import Empty

import uvicorn
from sqlalchemy import select, update

from config import BASE_PATH, RESOURCES_PATH
from core.enums import DeploymentStatus
from core.typing import DeploymentPayload
from db_models import Accounts, Deployments, StrategyVersions
from utils import get_db_sess_sync


logger = logging.getLogger(__name__)


def run_server(queue) -> None:
    print(queue)
    logger.info("Starting server.")
    import config

    config.DEPLOYMENT_QUEUE = queue
    uvicorn.run("server.app:app", port=80, host="localhost")  # , reload=True)


def _handle_deployment(payload: DeploymentPayload) -> None:
    with get_db_sess_sync() as db_sess:
        res = db_sess.execute(
            select(Deployments.instrument, Accounts.platform, StrategyVersions.code)
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

    # TODO: Build alternative solution
    mainpy = open(os.path.join(RESOURCES_PATH, "deployment.txt"), "r").read()
    mainpy = mainpy.format(
        strategy_code=data.code, instrument=data.instrument, parent_folder=BASE_PATH
    )
    print(mainpy)

    try:
        code = compile(mainpy, "<string>", "exec")
        res = exec(code)
    except Exception as e:
        print(type(e), str(e))

    # with TemporaryDirectory() as folder:
    #     print(mainpy)
    #     fp = os.path.join(folder, "main.py")
    #     open(fp, "w").write(mainpy)

    #     logger.info(f"Created main py file for deployment {payload.deployment_id}")
    #     logger.info(f"Running main py file for deployment {payload.deployment_id}")

    #     res = subprocess.run(["python", fp], capture_output=True)
    #     logger.info(f"Captured output for deployment {payload.deployment_id}")

    #     print(res)

    status = None

    # if res.returncode == 0:
    #     status = DeploymentStatus.STOPPED
    # else:
    #     status = DeploymentStatus.FAILED

    # with get_db_sess_sync() as db_sess:
    #     db_sess.execute(update(Deployments).values(status=status.value))
    #     db_sess.commit()


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
