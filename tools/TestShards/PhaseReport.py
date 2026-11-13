from __future__ import annotations

from typing import NamedTuple


class PhaseReport(NamedTuple):
    TestId: str
    Phase: str
    Outcome: str
    Seconds: float
