from abc import abstractmethod

from core.enums import StrategyType
from lib.enums import TradingPlatform
from lib.order_manager_registry import OrderManagerRegistry
from lib.typing import Tick


class Strategy:
    """
    Base class for all startegies. The run method is called
    when a new tick comes in
    """

    def __init__(
        self,
        *,
        type: StrategyType,
        platform: TradingPlatform,
        instrument: str,
        pip_size: float = 0.0001,
    ):
        self._type = type
        self._om = OrderManagerRegistry.get(platform)
        self._instrument = instrument
        self._pip_size = pip_size

    @abstractmethod
    def run(self, tick: Tick): ...

    def shutdown(self):
        """
        Contains any necessary shutdown logic. For example
        closing all positions and / or orders.
        """

    def startup(self):
        """
        Contains necessary startup logic. For example
        logging into platform, fetching previous information etc.
        """
        self._om.login()

    def __enter__(self):
        self.startup()
        return self

    def __exit__(self, exc_type, exc_value, tcb):
        self.shutdown()

    @property
    def type(self) -> StrategyType:
        return self._type
