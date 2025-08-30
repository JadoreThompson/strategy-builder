import ast
import uuid
import pandas as pd
from dataclasses import dataclass


class OrderManager:
    def place_order(self, **kw): ...


def bos(df: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    df = df.copy()
    df["bos"] = None

    for i in range(lookback, len(df)):
        # define swing high/low
        swing_high = df["high"][i - lookback : i].max()
        swing_low = df["low"][i - lookback : i].min()

        # bullish BOS: current close > swing high
        if df["close"].iloc[i] > swing_high:
            df.loc[df.index[i], "bos"] = "bullish"
        # bearish BOS: current close < swing low
        elif df["close"].iloc[i] < swing_low:
            df.loc[df.index[i], "bos"] = "bearish"

    return df


def fvg(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["fvg"] = None

    for i in range(2, len(df)):
        high1, low1 = df["high"].iloc[i - 2], df["low"].iloc[i - 2]
        high3, low3 = df["high"].iloc[i], df["low"].iloc[i]

        # Bullish FVG: low3 > high1
        if low3 > high1:
            df.loc[df.index[i], "fvg"] = "bullish"
        # Bearish FVG: high3 < low1
        elif high3 < low1:
            df.loc[df.index[i], "fvg"] = "bearish"

    return df


jl = {
    ">": [
        "price",
        {
            "query": {
                "max": ...,
                "where": ...,
            }
        },
    ],
    "action_chain": [
        {"type": "bos", "timeframe": "1m", "params": {}},
        {"type": "fvg", "timeframe": "1m", "params": {}},
    ],
    "execution": {
        "order_type": "limit",
        "side": "ask",
        "limit_price": "action_chain.1.below",
        "take_profit": ...,
        "stop_loss": ...,
    },
}


pycode = """
def myfunc(a: int):
    return a > 5
"""
# node = ast.parse(pycode)
# print(ast.dump(node, indent=4))
# exit()


# obj = {">": ["price", 5]}
# keys = list(obj.keys())
# left, right = obj[keys[0]]

# func = ast.FunctionDef(
#     name=f"ternary_{uuid.uuid4().hex[:6]}",
#     args=ast.arguments(
#         posonlyargs=[],
#         args=[ast.arg(arg="price", annotation=ast.Name(id="float", ctx=ast.Load()))],
#         kwonlyargs=[],
#         kw_defaults=[],
#         defaults=[]
#     ),
#     body=[
#         ast.Return(
#             value=ast.Compare(
#                 left=ast.Name(id="price", ctx=ast.Load()),
#                 ops=[ast.GtE()],
#                 comparators=[ast.Constant(value=right)]
#             )
#         )
#     ],
#     decorator_list=[]
# )

# print(ast.unparse(func))

import ast
import uuid

# Build the AST function (from previous example)
func = ast.FunctionDef(
    name=f"ternary_{uuid.uuid4().hex[:6]}",
    lineno=1,    
    args=ast.arguments(
        posonlyargs=[],
        args=[ast.arg(arg="price", annotation=ast.Name(id="float", ctx=ast.Load()))],
        kwonlyargs=[],
        kw_defaults=[],
        defaults=[]
    ),
    body=[
        ast.Return(
            value=ast.Compare(
                left=ast.Name(id="price", ctx=ast.Load()),
                ops=[ast.GtE()],
                comparators=[ast.Constant(value=5)]
            )
        )
    ],
    decorator_list=[]
)

# Wrap the function in a Module
module = ast.Module(body=[func], type_ignores=[])

# Convert AST to Python code
source_code = ast.unparse(module)
print(source_code)
