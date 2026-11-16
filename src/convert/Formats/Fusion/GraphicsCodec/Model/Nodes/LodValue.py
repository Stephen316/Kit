from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.NodePayload import NodePayload
from convert.Formats.Fusion.GraphicsCodec.Model.Values.SimpleMesh import SimpleMesh
from convert.Formats.Fusion.GraphicsCodec.Model.Values.FatPoint import FatPoint
from convert.Formats.Fusion.GraphicsCodec.Model.Values.EnhancedEdge import EnhancedEdge
from convert.Formats.Fusion.GraphicsCodec.Model.Values.EnhancedFace import EnhancedFace


# lod value needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class LodValue:
    NodeData: NodePayload
    LodMask: int
    Geometry: SimpleMesh | FatPoint | EnhancedEdge | EnhancedFace | None
    Bounds: tuple[float, ...]
    UseClosest: bool
