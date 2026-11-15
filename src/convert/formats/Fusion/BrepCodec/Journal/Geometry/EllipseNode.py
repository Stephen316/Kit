from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# ellipse node needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class EllipseNode:
    Prefix: EntityPrefix
    OriginCm: KJournalVector
    Normal: KJournalVector
    MajorAxisCm: KJournalVector
    EllipseRatio: float
    LowerBound: float | None
    UpperBound: float | None
