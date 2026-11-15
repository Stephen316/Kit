from dataclasses import dataclass as MakeDataClass

from interchange.features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.models.VectorSpace import SpaceVector


# the cut end code determines which typed operands may contribute geometry
@MakeDataClass(frozen=True, slots=True)
class CutEndData:
    EndValue: ExtrudeEnd
    FlagBits: int
    Direction: SpaceVector
    AlongId: int | None
    CacheId: int
    TaperId: int
    EndProxy: int | None
