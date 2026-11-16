from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# polyhedron needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class Polyhedron:
    PointsMm: tuple[KJournalVector, ...]
    FaceLoops: tuple[tuple[int, ...], ...]
    EntityTag: int = 0
