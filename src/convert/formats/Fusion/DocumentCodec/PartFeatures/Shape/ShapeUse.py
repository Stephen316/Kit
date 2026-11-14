from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeEdge import FreeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.RiseEdge import RiseEdge

KShapeEdge: TypeAlias = LevelEdge | RiseEdge | FreeEdge


@MakeDataClass(frozen=True, slots=True)
class ShapeUse:
    Edge: KShapeEdge
    Forward: bool
