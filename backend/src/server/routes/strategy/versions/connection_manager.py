import asyncio
import json
import logging
from collections import defaultdict

from aiokafka import AIOKafkaConsumer, ConsumerRecord
from fastapi import WebSocket
from pydantic import ValidationError
from starlette.websockets import WebSocketState

from config import KAFKA_HOST, KAFKA_PORT, KAFKA_POSITIONS_WEBSOCKET_TOPIC
from core.events import PositionEvent


logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._active_conns: dict[str, dict[str, WebSocket]] = defaultdict(dict)
        self._is_running = False
        self._fut = asyncio.Future()
        self._task: asyncio.Task | None = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def _start(self):
        consumer = AIOKafkaConsumer(
            KAFKA_POSITIONS_WEBSOCKET_TOPIC,
            bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
            group_id="my-group",
        )
        await consumer.start()

        self._is_running = True
        self._fut.set_result(True)

        try:
            m: ConsumerRecord
            async for m in consumer:
                try:
                    event = PositionEvent.model_validate_json(m.value)
                    if self._active_conns.get(event.user_id, {}).get(event.version_id):
                        ddict = event.to_serialisable_dict()
                        
                        ddict.pop("user_id")
                        ddict.pop("version_id")

                        await self._active_conns[event.user_id][
                            event.version_id
                        ].send_text(json.dumps(ddict))
                except ValidationError as e:
                    logger.debug(f"Validation Error: {str(e)}")
                    continue
                except Exception as e:
                    logger.info(
                        f"Unexpected error occured handling consumer payload - Error {type(e)} - {str(e)}"
                    )
        finally:
            await consumer.stop()

    async def connect(self, user_id: str, version_id: str, ws: WebSocket) -> None:
        if not self._is_running and not self._task:
            self._task = asyncio.create_task(self._start())
            await self._fut
            logger.info("Listening for messages")

        obj = self._active_conns[user_id]
        existing_ws = obj.get(version_id)
        if existing_ws and existing_ws.client_state != WebSocketState.DISCONNECTED:
            await existing_ws.close()

        obj[version_id] = ws
        logger.debug(
            "WebSocket connected. Active connections: %d", len(self._active_conns)
        )

    def disconnect(self, user_id: str, version_id: str) -> None:
        if user_id not in self._active_conns:
            return

        obj = self._active_conns[user_id]
        obj.pop(version_id, None)
        if not obj:
            self._active_conns.pop(user_id)

    def __del__(self):
        if self._task:
            self._task.cancel()
