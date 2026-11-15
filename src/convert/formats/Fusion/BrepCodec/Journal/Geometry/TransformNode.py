from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# transform node needs an explicit state contract so topology changes retain their native revision relationships
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
