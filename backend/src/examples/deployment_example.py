"""
An example of how deployments are done
"""

from decimal import Decimal

from sqlalchemy import select

from core.enums import OrderType, Side, StrategyType
from db_models import Ticks
from trading_lib import Strategy, TradingPlatform
from trading_lib.exchanges.mt5_futures_exchange import MT5FuturesExchange
from trading_lib.order_managers.mt5_futures_order_manager import (
    MT5FuturesOrderManager,
)
from trading_lib.typing import Tick
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
    import sys

    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

    exchange = MT5FuturesExchange({})
    om = MT5FuturesOrderManager()
    om._exchange = exchange

    strat = UserStrategy(StrategyType.FUTURES, TradingPlatform.MT5, "EURUSD")
    strat._om = om

    with strat:
        for tick in exchange.subscribe("EURUSD"):
            strat.run(tick)


if __name__ == "__main__":
    main()
