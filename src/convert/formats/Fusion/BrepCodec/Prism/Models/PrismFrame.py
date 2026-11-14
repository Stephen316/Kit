from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Prism.Models.PrismEdge import PrismEdge
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismPlane import PrismPlane


@MakeDataClass(frozen=True, slots=True)
class PrismFrame:
    CornersCm: tuple[tuple[float, float, float], ...]
    FaceOrder: tuple[int, ...]
    FaceStarts: tuple[int, ...]
    FaceReverse: tuple[bool, ...]
    Edges: tuple[PrismEdge, ...]
    VertexOwners: tuple[int, ...]
    Planes: tuple[PrismPlane, ...]
