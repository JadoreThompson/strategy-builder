from abc import abstractmethod

from lib.enums import TradingPlatform
from lib.order_manager_registry import OrderManagerRegistry
from lib.typing import Tick


class Strategy:
    """
    Base class for all startegies. The run method is called
    when a new tick comes in
    """

    def __init__(self, *, platform: TradingPlatform):
        self._om = OrderManagerRegistry.get(platform)

    @abstractmethod
    def run(self, tick: Tick): ...
