"""
An example of how backtests are run
"""

from decimal import Decimal

from sqlalchemy import select

from core.enums import OrderType, Side, StrategyType
from db_models import Ticks
from lib import Strategy, TradingPlatform
from lib.typing import Tick
from utils import get_db_sess_sync


class UserStrategy(Strategy):
    """
    A simple strategy that longs when the current tick
    price is lower than the previous and vice versa for shorts
    """

    def __init__(self, type, platform, instrument, pip_size=0.0001):
        super().__init__(
            type=type, platform=platform, instrument=instrument, pip_size=pip_size
        )
        self._last_price: float | None = None
        self._placed = False

    def startup(self):
        with get_db_sess_sync() as db_sess:
            prev_tick = db_sess.scalar(
                select(Ticks)
                .where(Ticks.instrument == self._instrument)
                .order_by(Ticks.time.desc())
                .limit(1)
            )

        if prev_tick:
            self._last_price = prev_tick.last_price

    def shutdown(self):
        self._om.cancel_all_positions()
        self._om.close_all_positions()

    def run(self, tick: Tick) -> None:
        if self._last_price is None or self._om.positions:
            self._last_price = tick.last
            return

        if tick.last < self._last_price:
            success = self._om.open_position(
                self._instrument,
                Side.BID,
                OrderType.MARKET,
                Decimal("10.0"),
                tp_price=1.13008,
            )
            if success:
                self._placed = True
        self._last_price = tick.last


def main():
    import os
    import pandas as pd
    import sys

    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
    from config import RESOURCES_PATH
    from lib import Backtest

    def startup(*args, **kw):
        nonlocal strat
        if not strat._om.login():
            raise ValueError("Unsuccessful login")

    fp = os.path.join(RESOURCES_PATH, "price-data", "EURUSD1.csv")
    eur_df = pd.read_csv(fp)
    eur_df.set_index("datetime", inplace=True)

    strat = UserStrategy(StrategyType.FUTURES, TradingPlatform.MT5, "EURUSD")
    strat.startup = startup
    bt = Backtest(strat, df=eur_df)
    results = bt.run()
    print(results)


if __name__ == "__main__":
    main()
