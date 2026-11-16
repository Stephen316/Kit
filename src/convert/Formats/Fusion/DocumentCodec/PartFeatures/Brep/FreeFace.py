from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel

# the free surface variants need one shared contract so feature geometry cannot omit a supported value shape
KFreeSurface: TypeAlias = PlaneNode | ConeNode | TorusNode


# free face needs an explicit state contract so edge and face relationships survive parametric feature construction
@MakeDataClass(frozen=True, slots=True)
class FreeFace:
    Surface: KFreeSurface
    Reversed: bool
    Label: FaceLabel
    Loops: tuple[tuple[ShapeUse, ...], ...]
