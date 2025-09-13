import asyncio
import logging

from aiokafka import AIOKafkaConsumer, ConsumerRecord
from fastapi import WebSocket

from config import KAFKA_HOST, KAFKA_PORT, KAFKA_POSITIONS_TOPIC


logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._active_conns = set()
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
                logger.info(f"Received: {m.value.decode()}")
        finally:
            await consumer.stop()

    async def connect(self, ws: WebSocket) -> None:
        if not self._is_running and not self._task:
            self._task = asyncio.create_task(self._start())
            await self._fut
            logger.info("Listening for messages")

        await ws.accept()
        self._active_conns.add(ws)
        logger.debug(
            "WebSocket connected. Active connections: %d", len(self._active_conns)
        )

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._active_conns:
            self._active_conns.remove(ws)
            logger.debug(
                "WebSocket disconnected. Active connections: %d",
                len(self._active_conns),
            )

    def __del__(self):
        if self._task:
            self._task.cancel()
