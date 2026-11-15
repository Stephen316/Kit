from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeEdge import FreeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.RiseEdge import RiseEdge

# the shape edge variants need one shared contract so parametric feature reconstruction cannot omit a supported value shape
KShapeEdge: TypeAlias = LevelEdge | RiseEdge | FreeEdge


# shape use needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class ShapeUse:
    Edge: KShapeEdge
    Forward: bool
