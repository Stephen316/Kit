from __future__ import annotations

from typing import NamedTuple


class ReuseChoice(NamedTuple):
    Run: str
    Outcomes: dict[str, str]
    Entries: dict[str, dict[str, object]]
    Reason: str
