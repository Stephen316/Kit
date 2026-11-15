from __future__ import annotations

from typing import NamedTuple


# reuse plan needs an explicit state contract so dependency changes cannot revive stale passing results
class ReusePlan(NamedTuple):
    Run: str
    Outcomes: dict[str, str]
    Seconds: dict[str, float]
    CollectedCount: int
