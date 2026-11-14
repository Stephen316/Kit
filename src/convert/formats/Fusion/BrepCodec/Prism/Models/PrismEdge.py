from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Prism.Models.PrismLine import PrismLine


@MakeDataClass(frozen=True, slots=True)
class PrismEdge:
    StartCorner: int
    EndCorner: int
    LowerParam: float
    UpperParam: float
    OwnerFace: int
    Curve: PrismLine
