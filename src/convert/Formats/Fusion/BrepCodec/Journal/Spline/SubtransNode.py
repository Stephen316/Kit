from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.Formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


# subtrans node needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class SubtransNode:
    Surface: TsplineSurface
    Regions: tuple[tuple[PatchCell, ...], ...]
