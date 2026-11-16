from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# sphere node needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class SphereNode:
    Prefix: EntityPrefix
    CenterCm: KJournalVector
    RadiusCm: float
    ReferenceAxis: KJournalVector
    PoleDirection: KJournalVector
    ReversedV: bool
    ULower: float | None
    UUpper: float | None
    VLower: float | None
    VUpper: float | None
