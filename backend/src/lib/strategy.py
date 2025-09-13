from abc import abstractmethod

from lib.order_managers.futures_order_manager import FuturesOrderManager
from core.enums import StrategyType
from lib.enums import TradingPlatform
from lib.typing import Tick


class Strategy:
    """
    Base class for all startegies. The run method is called
    when a new tick comes in
    """

    _om: FuturesOrderManager | None = None  # must be set after init

    def __init__(self, type: StrategyType, instrument: str, **kw):
        self._type = type
        self._instrument = instrument.lower()

    @abstractmethod
    def run(self, tick: Tick): ...

    def shutdown(self):
        """
        Contains any necessary shutdown logic. For example
        closing all positions and / or orders.
        """

    def startup(self):
        """
        Pretrade logic to be ran before receiving ticks
        """
        if not self._om:
            raise Exception("OM not initialised.")
        if not self._om.login():
            raise Exception("OM failed to login")

    def __enter__(self):
        self.startup()
        return self

    def __exit__(self, exc_type, exc_value, tcb):
        self.shutdown()

    @property
    def type(self) -> StrategyType:
        return self._type
