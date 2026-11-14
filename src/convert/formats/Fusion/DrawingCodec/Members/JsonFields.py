from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias


@MakeDataClass(frozen=True, slots=True)
class JsonFields:
    Items: tuple[tuple[str, KFrozenJson], ...]


KFrozenJson: TypeAlias = (
    None | bool | int | float | str | tuple["KFrozenJson", ...] | JsonFields
)
