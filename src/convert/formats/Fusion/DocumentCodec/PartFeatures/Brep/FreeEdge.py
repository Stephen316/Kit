from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    KSpaceVector,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel

KFreeCurve: TypeAlias = StraightNode | EllipseNode


@MakeDataClass(frozen=True, slots=True)
class FreeEdge:
    Curve: KFreeCurve
    LowerParam: float
    UpperParam: float
    StartCm: KSpaceVector
    FinishCm: KSpaceVector
    Label: FaceLabel | None = None
