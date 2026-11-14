from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)


@MakeDataClass(frozen=True, slots=True)
class PlanarShell:
    StateId: int
    BodyRef: int
    EntityTag: int
    VertexRefs: tuple[int, ...]
    PointsCm: tuple[KJournalVector, ...]
    FaceRefs: tuple[int, ...]
    Rings: tuple[tuple[int, ...], ...]
    VolumeCm3: float
    Placement: TransformNode | None = None
