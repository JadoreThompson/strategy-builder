import json
import logging
import os
import time
from asyncio import Queue
from queue import Empty

from kafka import KafkaConsumer, KafkaProducer
import uvicorn
from sqlalchemy import insert, select, update

from core.enums import DeploymentStatus
from config import (
    BASE_PATH,
    KAFKA_HOST,
    KAFKA_PORT,
    KAFKA_POSITIONS_LOGGER_TOPIC,
    KAFKA_POSITIONS_TOPIC,
    RESOURCES_PATH,
)
from core.typing import DeploymentPayload, PositionMessage
from db_models import Accounts, Deployments, Positions, StrategyVersions, Users
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
        version_id=data.version_id,
        deployment_id=payload.deployment_id,
        instrument=data.instrument,
        parent_folder=BASE_PATH,
        creds={"login": data.login, "password": data.password, "server": data.server},
        user_id=data.user_id,
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


def positions_logger() -> None:
    producer = KafkaProducer(
        bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
    )
    consumer = KafkaConsumer(
        KAFKA_POSITIONS_LOGGER_TOPIC,
        bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
        auto_offset_reset="earliest",
        group_id="my-group",
    )

    for m in consumer:
        data = PositionMessage(**json.loads(m.value.decode()))
        pdict = data.position.model_dump()

        if data.topic == "new":
            q = insert(Positions).values(**pdict)
        elif data.topic == "update":
            q = (
                update(Positions)
                .values(**pdict)
                .where(Positions.position_id == pdict["position_id"])
            )
        else:
            logger.warning(f"Unkown topic {data.topic}")
            continue

        with get_db_sess_sync() as db_sess:
            db_sess.execute(q)
            db_sess.commit()

        producer.send(KAFKA_POSITIONS_TOPIC, m.value)
