from __future__ import annotations

from typing import NamedTuple


class ReusePlan(NamedTuple):
    Run: str
    Outcomes: dict[str, str]
    Seconds: dict[str, float]
    CollectedCount: int
