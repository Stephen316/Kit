from __future__ import annotations

import os as OsLib
from functools import lru_cache as Memoize

KSkippedParts = frozenset(
    {".git", ".pytest_cache", ".venv", "__pycache__", "node_modules", "site-packages"}
)


@Memoize(maxsize=None)
def LocateFile(RootText: str, FullText: str) -> str | None:
    RealText = OsLib.path.realpath(FullText)
    if RealText + OsLib.sep == RootText:
        return ""
    if not RealText.startswith(RootText):
        return None
    RelText = RealText[len(RootText) :].replace(OsLib.sep, "/")
    if KSkippedParts.intersection(RelText.split("/")):
        return None
    return RelText
