from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    KSpaceVector,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel

# the free curve variants need one shared contract so feature geometry cannot omit a supported value shape
KFreeCurve: TypeAlias = StraightNode | EllipseNode


# free edge needs an explicit state contract so edge and face relationships survive parametric feature construction
@MakeDataClass(frozen=True, slots=True)
class FreeEdge:
    Curve: KFreeCurve
    LowerParam: float
    UpperParam: float
    StartCm: KSpaceVector
    FinishCm: KSpaceVector
    Label: FaceLabel | None = None
