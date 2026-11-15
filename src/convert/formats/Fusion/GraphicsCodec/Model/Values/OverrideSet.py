from dataclasses import dataclass as MakeDataClass
from typing import Generic
from convert.formats.Fusion.GraphicsCodec.Model.Values.AppliedSet import AppliedSet
from convert.formats.Fusion.GraphicsCodec.Model.Values.NodeTarget import NodeTarget
from convert.formats.Fusion.GraphicsCodec.Model.Values.KSetValue import KSetValue


# override set needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class OverrideSet(Generic[KSetValue]):
    SetValue: AppliedSet[KSetValue]
    Target: NodeTarget
    ChildSets: tuple[AppliedSet[KSetValue], ...]
