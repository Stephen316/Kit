from __future__ import annotations

from typing import NamedTuple


class TreeIndex(NamedTuple):
    Blobs: dict[str, str]
    Digests: dict[str, str]
