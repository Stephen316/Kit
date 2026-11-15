from __future__ import annotations

from collections import Counter
from typing import NamedTuple


# report tally needs an explicit state contract so every collected case receives exactly one verified outcome
class ReportTally(NamedTuple):
    Durations: dict[str, float]
    Outcomes: dict[str, str]
    SetupCounts: Counter[str]
    Unfinished: int
