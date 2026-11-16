from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.PrimitiveLod import PrimitiveLod
from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.LodValue import LodValue
from convert.Formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef


# sketch world needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class SketchWorld:
    FaceBody: BrepWorld | None
    Nodes: tuple[LodValue, ...]
    RegularNodes: tuple[ObjectRef | PrimitiveLod | None, ...] = ()
    NoCullingNodes: tuple[ObjectRef | PrimitiveLod | None, ...] = ()
