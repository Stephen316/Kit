from __future__ import annotations

from typing import NamedTuple


# tree index needs an explicit state contract so dependency changes cannot revive stale passing results
class TreeIndex(NamedTuple):
    Blobs: dict[str, str]
    Digests: dict[str, str]
