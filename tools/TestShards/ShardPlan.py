from __future__ import annotations

from typing import NamedTuple


class ShardPlan(NamedTuple):
    Index: int
    TestIds: tuple[str, ...]
    Estimate: float
