from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# cone node needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class ConeNode:
    Prefix: EntityPrefix
    OriginCm: KJournalVector
    AxisVector: KJournalVector
    MajorAxisCm: KJournalVector
    EllipseRatio: float
    EllipseLower: float | None
    EllipseUpper: float | None
    SineAngle: float
    CosineAngle: float
    UScaleCm: float
    Reversed: bool
    ULower: float | None
    UUpper: float | None
    VLower: float | None
    VUpper: float | None
