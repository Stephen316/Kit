from __future__ import annotations

from typing import NamedTuple


# phase report needs an explicit state contract so every collected case receives exactly one verified outcome
class PhaseReport(NamedTuple):
    TestId: str
    Phase: str
    Outcome: str
    Seconds: float
