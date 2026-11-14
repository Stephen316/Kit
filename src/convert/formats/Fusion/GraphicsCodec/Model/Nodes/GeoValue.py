from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.RenderFrame import RenderFrame
from convert.formats.Fusion.GraphicsCodec.Model.Values.SimpleMesh import SimpleMesh
from convert.formats.Fusion.GraphicsCodec.Model.Values.FatPoint import FatPoint


@MakeDataClass(frozen=True, slots=True)
class GeoValue:
    Frame: RenderFrame
    Geometry: SimpleMesh | FatPoint | None
    Bounds: tuple[float, ...]
