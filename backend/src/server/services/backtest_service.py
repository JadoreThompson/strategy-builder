import json
import os
import subprocess
import sys
import tempfile
from typing import TypedDict
from uuid import UUID

from config import BASE_PATH


class BakcktestParams(TypedDict):
    backtest_id: UUID
    instrument: str
    leverage: int
    starting_balance: float


class BacktestService:
    @staticmethod
    def _create_runner_script(
        strategy_code: str, backtest_params: BakcktestParams
    ) -> str:
        runner_template = f"""
import json
import os
import sys
import pandas as pd
from decimal import Decimal

sys.path.append(r"{BASE_PATH}")

from config import RESOURCES_PATH
from core.enums import StrategyType
from lib import Backtest
from lib.enums import TradingPlatform

{strategy_code}

def run():
    fp = os.path.join(RESOURCES_PATH, "price-data", "EURUSD1.csv")
    data_df = pd.read_csv(fp)
    if "datetime" in data_df.columns:
        data_df["datetime"] = pd.to_datetime(data_df["datetime"])
        data_df.set_index("datetime", inplace=True)

    strat = UserStrategy(
        type=StrategyType.FUTURES,
        instrument="{backtest_params['instrument']}"
    )
    
    bt = Backtest(
        "{backtest_params['backtest_id']}",
        strat, 
        df=data_df, 
        starting_balance={backtest_params['starting_balance']},
        leverage={backtest_params['leverage']}
    )
    results = bt.run()
    
    print(results.model_dump_json())

if __name__ == "__main__":
    run()
"""

        return runner_template

    @staticmethod
    def _parse_output(output: str) -> dict:
        result: dict = json.loads(output)

        for key in ("total_pnl", "starting_balance", "end_balance"):
            result[key] = round(float(result[key]), 2)
        
        result["win_rate"] *= 100
        backtest_id = result["backtest_id"]

        for pos in result["positions"]:
            pos["backtest_id"] = backtest_id
            for key in (
                "starting_amount",
                "current_amount",
                "unrealised_pnl",
                "realised_pnl",
            ):
                pos[key] = round(float(pos[key]), 2)

        return result

    def run(self, strategy_code: str, backtest_params: BakcktestParams) -> dict:
        with tempfile.TemporaryDirectory() as tmpdir:
            runner_script_content = self._create_runner_script(
                strategy_code, backtest_params
            )

            script_path = os.path.join(tmpdir, "backtest_runner.py")
            with open(script_path, "w") as f:
                f.write(runner_script_content)

            process = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                check=False,
            )

            if process.returncode != 0:
                raise Exception(f"Backtest execution failed: {process.stderr}")

            return self._parse_output(process.stdout)
