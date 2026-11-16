from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# poly layout needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class PolyLayout:
    PointsCm: tuple[KJournalVector, ...]
    FaceLoops: tuple[tuple[int, ...], ...]
    Edges: tuple[tuple[int, int], ...]
    LoopStarts: tuple[int, ...]
    FaceBase: int
    LoopBase: int
    CoedgeBase: int
    EdgeBase: int
    VertexBase: int
    PointBase: int
    PlaneBase: int
    CurveBase: int
