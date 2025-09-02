import pandas as pd

from lib.typing import BacktestResult, Tick
from .strategy import Strategy
from .order_managers import BacktestFuturesOrderManager


# TODO: Open and close trades on tick levels.
class Backtest:
    """
    To be used to perform a backtest, evaluating
    the performance of strategy on experimental data.
    """
    def __init__(
        self, strat: Strategy, df_path: str, starting_balance: float = 100_000
    ) -> None:
        self._starting_balance = starting_balance
        strat._om = BacktestFuturesOrderManager(starting_balance=starting_balance)
        self._strat = strat
        self._df_path = df_path

    def run(self) -> BacktestResult:
        reader = pd.read_csv(self._df_path, chunksize=1000)
        for chunk in reader:
            for dt, row in chunk.iterrows():
                tick = Tick(last=row["close"], time=dt)
                self._strat.run(tick)

        om = self._strat._om
        closed_count = len(om._closed_positions)

        total_trades = len(om._positions) + closed_count
        win_rate = sum(
            1
            for pos in om._closed_positions
            if pos.realised_pnl and pos.realised_pnl >= 0.0
        )

        total_pnl = 0.0
        for pos in om._closed_positions:
            total_pnl += pos.realised_pnl

        for pos in om._positions.values():
            total_pnl += pos.realised_pnl

        res = BacktestResult(
            total_pnl=total_pnl,
            starting_balance=self._starting_balance,
            end_balance=om._balance,
            total_trades=total_trades,
            win_rate=win_rate,
        )
        return res
