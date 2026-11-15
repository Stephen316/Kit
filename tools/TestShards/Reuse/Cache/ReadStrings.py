from __future__ import annotations

from typing import cast as CastValue


# the strings operation needs a distinct decoding boundary so dependency changes cannot revive stale passing results
def ReadStrings(Value: object, Label: str) -> list[str]:
    if not isinstance(Value, list):
        raise ValueError(f"{Label} is not a list")
    Members = CastValue(list[object], Value)
    Texts = [Member for Member in Members if isinstance(Member, str)]
    if len(Texts) != len(Members):
        raise ValueError(f"{Label} has a value that is not text")
    return Texts
