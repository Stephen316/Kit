from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.NodePayload import NodePayload


@MakeDataClass(frozen=True, slots=True)
class PrimitiveLod:
    NodeData: NodePayload
    LodMask: int
    Geometry: ObjectRef | None
    Bounds: tuple[float, ...]
    UseClosest: bool
    Primitive: ObjectRef | None
