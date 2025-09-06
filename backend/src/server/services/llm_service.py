class LLMService:
    @staticmethod
    async def generate_code(prompt: str) -> str:
        """
        Fetches a code gen response from LLM.

        For now mocks a call to an LLM API to generate strategy code based on the prompt.
        In a real application, this would call an external API like OpenAI.

        Returns:
            str: Raw prompt output
        """
        example_code = """from decimal import Decimal
from collections import deque

from core.enums import OrderType, Side, StrategyType
from lib import Strategy, TradingPlatform
from lib.typing import Tick

class UserStrategy(Strategy):
    \"\"\"
    A strategy that longs when the price is greater than the average of the last 3
    prices and shorts when it is lower.
    \"\"\"
    def __init__(self, type, platform, instrument, pip_size=0.0001, avg_period=3):
        super().__init__(
            type=type, platform=platform, instrument=instrument, pip_size=pip_size
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
