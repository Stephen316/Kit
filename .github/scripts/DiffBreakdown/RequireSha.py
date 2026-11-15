from __future__ import annotations

import re as Regex


# invalid sha input must fail here so published evidence stays bound to the reviewed revision
def RequireSha(ValueText: str) -> str:
    if Regex.fullmatch(r"[0-9a-f]{40}", ValueText) is None:
        raise ValueError("Expected a full Git commit SHA")
    return ValueText
