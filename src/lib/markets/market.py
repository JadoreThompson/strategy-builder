from abc import abstractmethod

from lib.typing import Tick


class Market:
    @abstractmethod
    @classmethod
    def get_tick(cls, instrument: str) -> Tick: ...
