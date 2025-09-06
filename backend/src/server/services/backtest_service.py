import os
import subprocess
import sys
import tempfile
from decimal import Decimal
from typing import TypedDict

from config import BASE_PATH
from core.enums import StrategyType
from lib.enums import TradingPlatform


class BakcktestParams(TypedDict):
    instrument: str
    leverage: int
    starting_balance: float


class BacktestService:
    @staticmethod
    def _create_runner_script(
        strategy_code: str, backtest_params: BakcktestParams
    ) -> str:
        runner_template = f"""
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
        platform=TradingPlatform.MT5,
        instrument="{backtest_params['instrument']}"
    )
    
    bt = Backtest(
        strat, 
        df=data_df, 
        starting_balance={backtest_params['starting_balance']},
        leverage={backtest_params['leverage']}
    )
    results = bt.run()
    
    # Print results in a machine-readable format for parsing
    print(f"PNL:{{results.total_pnl}}")
    print(f"START_BALANCE:{{results.starting_balance}}")
    print(f"END_BALANCE:{{results.end_balance}}")
    print(f"TOTAL_TRADES:{{results.total_trades}}")
    print(f"WIN_RATE:{{results.win_rate}}")

if __name__ == "__main__":
    run()
"""
        return runner_template

    @staticmethod
    def _parse_output(output: str) -> dict:
        results = {}
        for line in output.strip().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                key_map = {
                    "PNL": "total_pnl",
                    "START_BALANCE": "starting_balance",
                    "END_BALANCE": "end_balance",
                    "TOTAL_TRADES": "total_trades",
                    "WIN_RATE": "win_rate",
                }
                db_key = key_map.get(key.strip())
                if db_key:
                    val = value.strip()
                    if db_key in ["total_pnl", "starting_balance", "end_balance"]:
                        results[db_key] = Decimal(val)
                    elif db_key == "total_trades":
                        results[db_key] = int(val)
                    elif db_key == "win_rate":
                        results[db_key] = float(val)
        return results

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
