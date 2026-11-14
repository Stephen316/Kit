from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


@MakeDataClass(frozen=True, slots=True)
class TransformNode:
    Attribute: int
    EntityTag: int
    ColumnX: KJournalVector
    ColumnY: KJournalVector
    ColumnZ: KJournalVector
    TranslationCm: KJournalVector
    ScaleFactor: float
    HasRotation: bool
    HasReflection: bool
    HasShear: bool
