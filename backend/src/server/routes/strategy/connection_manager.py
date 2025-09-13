import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, ConsumerRecord
from fastapi import WebSocket
from starlette.websockets import WebSocketState

from core.typing import PositionMessage
from config import KAFKA_HOST, KAFKA_PORT, KAFKA_POSITIONS_TOPIC


logger = logging.getLogger(__name__)


class ExistingConnection(Exception):
    pass


class ConnectionManager:
    def __init__(self):
        self._active_conns: dict[str, WebSocket] = {}
        self._is_running = False
        self._fut = asyncio.Future()
        self._task: asyncio.Task | None = None

    async def _start(self):
        print(f"{KAFKA_HOST}:{KAFKA_PORT}")
        consumer = AIOKafkaConsumer(
            KAFKA_POSITIONS_TOPIC,
            bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
            auto_offset_reset="earliest",
            group_id="my-group",
        )
        await consumer.start()

        self._is_running = True
        self._fut.set_result(True)

        try:
            m: ConsumerRecord
            async for m in consumer:
                decoded = m.value.decode()
                data = PositionMessage(**json.loads(decoded))
                if data.user_id in self._active_conns:
                    await self._active_conns[data.user_id].send_text(decoded)

        finally:
            await consumer.stop()

    async def connect(self, user_id: str, version_id: str, ws: WebSocket) -> None:
        if not self._is_running and not self._task:
            self._task = asyncio.create_task(self._start())
            await self._fut
            logger.info("Listening for messages")

        key = (user_id, version_id)

        if key in self._active_conns:
            existing_ws = self._active_conns[key]
            if existing_ws.client_state != WebSocketState.DISCONNECTED:
                await existing_ws.close()

        await ws.accept()
        self._active_conns[key] = ws
        logger.debug(
            "WebSocket connected. Active connections: %d", len(self._active_conns)
        )

    def disconnect(self, user_id: str, version_id: str) -> None:
        key = (user_id, version_id)

        if key in self._active_conns:
            self._active_conns.pop(key)
            logger.debug(
                "WebSocket disconnected. Active connections: %d",
                len(self._active_conns),
            )

    def __del__(self):
        if self._task:
            self._task.cancel()
