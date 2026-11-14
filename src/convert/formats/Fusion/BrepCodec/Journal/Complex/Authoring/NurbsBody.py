from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


@MakeDataClass(frozen=True, slots=True)
class PlaneCarrier:
    OriginCm: KJournalVector
    Normal: KJournalVector
    ReferenceAxis: KJournalVector


@MakeDataClass(frozen=True, slots=True)
class CylinderCarrier:
    OriginCm: KJournalVector
    AxisVector: KJournalVector
    MajorAxisCm: KJournalVector


KFaceCarrier: TypeAlias = BsSurface | PlaneCarrier | CylinderCarrier


@MakeDataClass(frozen=True, slots=True)
class NurbsEdge:
    StartVertex: int
    EndVertex: int
    Curve: BsCurve
    Bounds: tuple[float, float] | None = None


@MakeDataClass(frozen=True, slots=True)
class NurbsUse:
    EdgeIndex: int
    Reversed: bool
    Pcurve: BsCurve | None
    OffsetU: float = 0.0
    OffsetV: float = 0.0


@MakeDataClass(frozen=True, slots=True)
class NurbsFace:
    Surface: KFaceCarrier
    Uses: tuple[NurbsUse, ...]
    Holes: tuple[tuple[NurbsUse, ...], ...] = ()


@MakeDataClass(frozen=True, slots=True)
class NurbsBody:
    PointsCm: tuple[KJournalVector, ...]
    Edges: tuple[NurbsEdge, ...]
    Faces: tuple[NurbsFace, ...]
    EntityTag: int = -1
