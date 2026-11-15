from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# plane node needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class PlaneNode:
    Prefix: EntityPrefix
    OriginCm: KJournalVector
    Normal: KJournalVector
    ReferenceAxis: KJournalVector
    ReversedV: bool
    ULower: float | None
    UUpper: float | None
    VLower: float | None
    VUpper: float | None
