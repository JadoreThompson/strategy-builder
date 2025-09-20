from abc import abstractmethod
from typing import Generator

from trading_lib.typing import Tick


class Exchange:
    """ABC for all exchanges"""
    def __init__(self, login_creds: dict):
        self._last_tick: Tick | None = None
        self._login_creds = login_creds

    @abstractmethod
    def login(self) -> bool:
        """
        Performs the requiring login process

        Returns:
            bool: True if successful login
        """

    @abstractmethod
    def subscribe(self, instrument: str) -> Generator[Tick, None, None]:
        """
        Subscribes to price stream and yields the ticks

        Args:
            instrument (str): Instrument to subscribe to

        Yields:
            Generator[Tick, None, None]: Tick object
        """

    @property
    def last_tick(self) -> Tick | None:
        return self._last_tick
