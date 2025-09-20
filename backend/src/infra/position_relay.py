import json
import logging

from kafka import KafkaConsumer, KafkaProducer
from pydantic import ValidationError
from sqlalchemy import insert, update

from core.enums import CoreEventType
from config import (
    KAFKA_HOST,
    KAFKA_PORT,
    KAFKA_POSITIONS_LOGGER_TOPIC,
    KAFKA_POSITIONS_LOGGER_TOPIC_GROUP,
    KAFKA_POSITIONS_WEBSOCKET_TOPIC,
)
from core.events import CoreEvent, PositionEvent
from db_models import Positions
from utils import get_db_sess_sync


logger = logging.getLogger(__name__)


class PositionRelay:
    """
    Consumes PositionEvent from the Strategy class, logs
    the position and relays to the
    """

    def __init__(self):
        self._producer = KafkaProducer(
            bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
        )
        self._consumer = KafkaConsumer(
            KAFKA_POSITIONS_LOGGER_TOPIC,
            bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
            group_id=KAFKA_POSITIONS_LOGGER_TOPIC_GROUP,
        )

    def listen(self):
        for m in self._consumer:
            try:
                ev = CoreEvent[PositionEvent](**json.loads(m.value.decode()))
                if ev.event_type != CoreEventType.POSITION_EVENT:
                    logger.info(f"Incorrect event type receied '{ev.event_type.name}'")
                    continue
                
                self.log_event(ev.data)
                self.relay_event(ev.data)
            except ValidationError:
                continue

    def log_event(self, event: PositionEvent) -> None:
        pdict = event.position.to_serialisable_dict()
        pdict["user_id"] = event.user_id
        pdict["version_id"] = event.version_id

        if event.type == "new":
            q = insert(Positions).values(**pdict)
        elif event.type == "update":
            q = (
                update(Positions)
                .values(**pdict)
                .where(Positions.position_id == pdict["position_id"])
            )
        else:
            logger.warning(f"Unkown topic {event.type}")
            return

        with get_db_sess_sync() as db_sess:
            db_sess.execute(q)
            db_sess.commit()

    def relay_event(self, event: PositionEvent) -> None:
        self._producer.send(
            KAFKA_POSITIONS_WEBSOCKET_TOPIC,
            json.dumps(event.model_dump_json()).encode(),
        )
