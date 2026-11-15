from dataclasses import dataclass as MakeDataClass
from typing import Generic
from convert.formats.Fusion.GraphicsCodec.Model.Values.KSetValue import KSetValue


# applied set needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class AppliedSet(Generic[KSetValue]):
    SetValue: KSetValue
    ApplyTypes: tuple[int, ...] | None
