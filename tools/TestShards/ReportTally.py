from __future__ import annotations

from collections import Counter
from typing import NamedTuple


class ReportTally(NamedTuple):
    Durations: dict[str, float]
    Outcomes: dict[str, str]
    SetupCounts: Counter[str]
    Unfinished: int
