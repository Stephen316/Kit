from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismLine import PrismLine


# prism edge needs an explicit state contract so profile topology remains connected to its extrusion history
@MakeDataClass(frozen=True, slots=True)
class PrismEdge:
    StartCorner: int
    EndCorner: int
    LowerParam: float
    UpperParam: float
    OwnerFace: int
    Curve: PrismLine
