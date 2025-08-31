from lib.typing import Tick


class MT5Market:
    @classmethod
    def get_tick(cls, instrument: str) -> Tick: ...