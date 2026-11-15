from __future__ import annotations

from typing import NamedTuple


# shard plan needs an explicit state contract so every collected case receives exactly one verified outcome
class ShardPlan(NamedTuple):
    Index: int
    TestIds: tuple[str, ...]
    Estimate: float
