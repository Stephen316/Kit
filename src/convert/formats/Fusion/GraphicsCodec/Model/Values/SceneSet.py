from __future__ import annotations
from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.GraphicAttr import GraphicAttr
from convert.formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef
from convert.formats.Fusion.GraphicsCodec.Model.Values.AppliedSet import AppliedSet


@MakeDataClass(frozen=True, slots=True)
class SceneSet:
    SetKind: int
    FlagsValue: int = 0
    RemovedFlags: int = 0
    AppendTypes: tuple[int, ...] = ()
    Attributes: tuple[GraphicAttr[SceneSet], ...] = ()
    ExternalRef: EntityRef | None = None
    NodeRef: str | None = None
    ChildSets: tuple[AppliedSet[SceneSet], ...] = ()
