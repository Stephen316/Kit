from convert.formats.Fusion.GraphicsCodec.Model.Nodes.PrimitiveLod import PrimitiveLod
from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.LodValue import LodValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef


@MakeDataClass(frozen=True, slots=True)
class SketchWorld:
    FaceBody: BrepWorld | None
    Nodes: tuple[LodValue, ...]
    RegularNodes: tuple[ObjectRef | PrimitiveLod | None, ...] = ()
    NoCullingNodes: tuple[ObjectRef | PrimitiveLod | None, ...] = ()
