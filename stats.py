from collections import namedtuple
from typing import Optional

Stats = namedtuple("Stats", "tmax tmin precip")

def fmt(x: Optional[float]) -> str:
    return "NA" if x is None else f"{x:.1f}"