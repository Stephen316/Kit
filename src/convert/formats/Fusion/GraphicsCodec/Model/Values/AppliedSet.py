from dataclasses import dataclass as MakeDataClass
from typing import Generic
from convert.formats.Fusion.GraphicsCodec.Model.Values.KSetValue import KSetValue


@MakeDataClass(frozen=True, slots=True)
class AppliedSet(Generic[KSetValue]):
    SetValue: KSetValue
    ApplyTypes: tuple[int, ...] | None
