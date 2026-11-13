from __future__ import annotations

from typing import NamedTuple


class CacheData(NamedTuple):
    Run: str
    Guard: dict[str, object]
    Modules: dict[str, dict[str, object]]
