from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismLine import PrismLine


# region edge needs an explicit state contract so supporting records retain their owning document relationships
@MakeDataClass(frozen=True, slots=True)
class RegionEdge:
    LowerParam: float
    UpperParam: float
    Curve: PrismLine
