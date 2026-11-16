from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismPlane import PrismPlane
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionEdge import (
    RegionEdge,
)


# region frame needs an explicit state contract so supporting records retain their owning document relationships
@MakeDataClass(frozen=True, slots=True)
class RegionFrame:
    CornersCm: tuple[tuple[float, float, float], ...]
    Edges: tuple[RegionEdge, ...]
    VertexOwners: tuple[int, ...]
    Plane: PrismPlane
    CoedgeTags: tuple[SketchLink, ...]
    EdgeTags: tuple[SketchLink, ...]
