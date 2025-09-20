from aiohttp import ClientSession

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME, SYSTEM_PROMPT


class LLMService:
    _http_sess: ClientSession | None = None

    @staticmethod
    async def generate_sample_code(prompt: str) -> str:
        """
        """
        example_code = """
from collections import deque
from decimal import Decimal

from core.enums import OrderType, Side, StrategyType
from lib import Strategy, TradingPlatform
from lib.typing import Tick

class UserStrategy(Strategy):
    \"\"\"
    A strategy that longs when the price is greater than the average of the last 3
    prices and shorts when it is lower.
    \"\"\"
    def __init__(self, type, platform, instrument, avg_period=3):
        super().__init__(
            type=type, platform=platform, instrument=instrument
        )
        self._prices = deque(maxlen=avg_period)
        self._avg_period = avg_period
        self._average = 0.0

    def shutdown(self):
        self._om.cancel_all_positions()
        self._om.close_all_positions()

    def run(self, tick: Tick) -> None:
        self._prices.append(tick.last)

        if len(self._prices) < self._avg_period:
            return
        
        self._average = sum(self._prices) / len(self._prices)

        if len(self._om.positions) > 0:
            return

        if tick.last > self._average:
            self._om.open_position(
                self._instrument,
                Side.BID, # Long
                OrderType.MARKET,
                Decimal("1.0"),
            )
        elif tick.last < self._average:
            self._om.open_position(
                self._instrument,
                Side.ASK, # Short
                OrderType.MARKET,
                Decimal("1.0"),
            )
"""
        return example_code

    @classmethod
    async def generate_code(cls, prompt: str) -> tuple[bool, str]:
        # TODO: Support streaming
        if cls._http_sess is None:
            cls._http_sess = ClientSession(
                base_url=LLM_BASE_URL + "/",
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            )

        rsp = await cls._http_sess.post(
            "chat/completions",
            json={
                "model": LLM_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            },
        )

        if rsp.status == 200:
            data = await rsp.json()
            return (True, data["choices"][0]["message"]["content"])
        return (False, f"Error code {rsp.status}")

    @staticmethod
    def clean_code(raw_code: str) -> str:
        """
        Cleans the raw output from an LLM, e.g., removing markdown fences.
        """
        if raw_code.startswith("```python"):
            raw_code = raw_code[len("```python") :]
        if raw_code.endswith("```"):
            raw_code = raw_code[: -len("```")]
        return raw_code.strip()
