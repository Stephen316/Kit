from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismPlane import PrismPlane
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionEdge import (
    RegionEdge,
)


@MakeDataClass(frozen=True, slots=True)
class RegionFrame:
    CornersCm: tuple[tuple[float, float, float], ...]
    Edges: tuple[RegionEdge, ...]
    VertexOwners: tuple[int, ...]
    Plane: PrismPlane
    CoedgeTags: tuple[SketchLink, ...]
    EdgeTags: tuple[SketchLink, ...]
