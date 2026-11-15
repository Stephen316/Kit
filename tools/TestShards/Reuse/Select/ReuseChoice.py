from __future__ import annotations

from typing import NamedTuple


# reuse choice needs an explicit state contract so dependency changes cannot revive stale passing results
class ReuseChoice(NamedTuple):
    Run: str
    Outcomes: dict[str, str]
    Entries: dict[str, dict[str, object]]
    Reason: str
