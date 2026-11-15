from __future__ import annotations

from typing import NamedTuple


# cache data needs an explicit state contract so dependency changes cannot revive stale passing results
class CacheData(NamedTuple):
    Run: str
    Guard: dict[str, object]
    Modules: dict[str, dict[str, object]]
