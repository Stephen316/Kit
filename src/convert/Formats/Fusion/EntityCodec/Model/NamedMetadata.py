from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# named metadata needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class NamedMetadata:
    FieldName: str
    TypeName: str
    Value: KEntityValue
    ElementName: str = ""
