from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


@MakeDataClass(frozen=True, slots=True)
class TorusNode:
    Prefix: EntityPrefix
    CenterCm: KJournalVector
    AxisVector: KJournalVector
    MajorRadiusCm: float
    MinorRadiusCm: float
    ReferenceAxis: KJournalVector
    ReversedV: bool
    ULower: float | None
    UUpper: float | None
    VLower: float | None
    VUpper: float | None
