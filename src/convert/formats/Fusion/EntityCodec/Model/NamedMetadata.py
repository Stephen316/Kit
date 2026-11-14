from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


@MakeDataClass(frozen=True, slots=True)
class NamedMetadata:
    FieldName: str
    TypeName: str
    Value: KEntityValue
    ElementName: str = ""
