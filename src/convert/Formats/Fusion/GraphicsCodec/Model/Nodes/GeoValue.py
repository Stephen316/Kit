from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.RenderFrame import RenderFrame
from convert.Formats.Fusion.GraphicsCodec.Model.Values.SimpleMesh import SimpleMesh
from convert.Formats.Fusion.GraphicsCodec.Model.Values.FatPoint import FatPoint


# geo value needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class GeoValue:
    Frame: RenderFrame
    Geometry: SimpleMesh | FatPoint | None
    Bounds: tuple[float, ...]
