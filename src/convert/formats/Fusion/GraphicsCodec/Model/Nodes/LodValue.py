from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.NodePayload import NodePayload
from convert.formats.Fusion.GraphicsCodec.Model.Values.SimpleMesh import SimpleMesh
from convert.formats.Fusion.GraphicsCodec.Model.Values.FatPoint import FatPoint
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedEdge import EnhancedEdge
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedFace import EnhancedFace


@MakeDataClass(frozen=True, slots=True)
class LodValue:
    NodeData: NodePayload
    LodMask: int
    Geometry: SimpleMesh | FatPoint | EnhancedEdge | EnhancedFace | None
    Bounds: tuple[float, ...]
    UseClosest: bool
