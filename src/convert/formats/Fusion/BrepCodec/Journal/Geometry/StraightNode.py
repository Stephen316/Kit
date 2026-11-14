from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


@MakeDataClass(frozen=True, slots=True)
class StraightNode:
    Prefix: EntityPrefix
    OriginCm: KJournalVector
    DirectionVector: KJournalVector
    LowerBound: float | None
    UpperBound: float | None
