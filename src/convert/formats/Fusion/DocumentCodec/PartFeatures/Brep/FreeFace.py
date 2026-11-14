from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel

KFreeSurface: TypeAlias = PlaneNode | ConeNode | TorusNode


@MakeDataClass(frozen=True, slots=True)
class FreeFace:
    Surface: KFreeSurface
    Reversed: bool
    Label: FaceLabel
    Loops: tuple[tuple[ShapeUse, ...], ...]
