from dataclasses import dataclass as MakeDataClass
from typing import Generic
from convert.formats.Fusion.GraphicsCodec.Model.Values.AppliedSet import AppliedSet
from convert.formats.Fusion.GraphicsCodec.Model.Values.NodeTarget import NodeTarget
from convert.formats.Fusion.GraphicsCodec.Model.Values.KSetValue import KSetValue


@MakeDataClass(frozen=True, slots=True)
class OverrideSet(Generic[KSetValue]):
    SetValue: AppliedSet[KSetValue]
    Target: NodeTarget
    ChildSets: tuple[AppliedSet[KSetValue], ...]
