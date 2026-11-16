from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias


# json fields needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class JsonFields:
    Items: tuple[tuple[str, KFrozenJson], ...]


# the frozen json variants need one shared contract so drawing packages cannot omit a supported value shape
KFrozenJson: TypeAlias = (
    None | bool | int | float | str | tuple["KFrozenJson", ...] | JsonFields
)
