from dataclasses import dataclass


@dataclass
class Tick:
    last: float  # Last traded price
    bid: float
    ask: float
