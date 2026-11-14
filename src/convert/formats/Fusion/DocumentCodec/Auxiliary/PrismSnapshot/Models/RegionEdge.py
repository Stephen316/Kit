from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Prism.Models.PrismLine import PrismLine


@MakeDataClass(frozen=True, slots=True)
class RegionEdge:
    LowerParam: float
    UpperParam: float
    Curve: PrismLine
