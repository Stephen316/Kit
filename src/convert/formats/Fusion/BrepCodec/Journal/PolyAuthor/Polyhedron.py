from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


@MakeDataClass(frozen=True, slots=True)
class Polyhedron:
    PointsMm: tuple[KJournalVector, ...]
    FaceLoops: tuple[tuple[int, ...], ...]
    EntityTag: int = 0
