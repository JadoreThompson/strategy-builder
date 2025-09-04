from decimal import Decimal

import pandas as pd

from core.enums import OrderType, PositionStatus
from lib.exchanges import BacktestFuturesExchange
from lib.typing import BacktestResult
from .order_managers import BacktestFuturesOrderManager
from .strategy import Strategy


class Backtest:
    """
    To be used to perform a backtest, evaluating
    the performance of strategy on experimental data.
    """

    def __init__(
        self,
        strat: Strategy,
        df_path: str | None = None,
        df: pd.DataFrame | None = None,
        starting_balance: float = 100_000,
        leverage: int = 10,
    ) -> None:
        self._starting_balance = starting_balance
        self._om = BacktestFuturesOrderManager(
            starting_balance=starting_balance, leverage=leverage
        )
        self._om._exchange = BacktestFuturesExchange({}, df_path, df)
        strat._om = self._om
        self._strat = strat

    def run(self) -> BacktestResult:
        for tick in self._om._exchange.subscribe(""):
            # Placing and closing trades
            positions = list(self._om._positions.values())
            for pos in positions:
                if pos.status == PositionStatus.OPEN:
                    if (pos.sl_price is not None and pos.sl_price == tick.last) or (
                        pos.tp_price is not None and pos.tp_price == tick.last
                    ):
                        self._om.close_position(pos.id, tick.last, pos.current_amount)
                elif pos.order_type in (OrderType.LIMIT, OrderType.STOP):
                    pos.status = PositionStatus.OPEN

            self._om.perform_risk_checks(tick)
            self._strat.run(tick)

        return self._get_backtest_result()

    def _get_backtest_result(self):
        closed_count = len(self._om._closed_positions)
        total_trades = len(self._om._positions) + closed_count
        win_rate = sum(
            1
            for pos in self._om._closed_positions
            if pos.realised_pnl and pos.realised_pnl >= 0.0
        )

        total_pnl = Decimal("0.0")
        for pos in self._om._closed_positions:
            total_pnl += pos.realised_pnl

        for pos in self._om.positions:
            total_pnl += pos.realised_pnl

        res = BacktestResult(
            total_pnl=total_pnl,
            starting_balance=self._starting_balance,
            end_balance=self._om._balance,
            total_trades=total_trades,
            win_rate=win_rate,
        )
        return res
