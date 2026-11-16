from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias

from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# plane carrier needs an explicit state contract so nested spline and surface records retain their relationships
@MakeDataClass(frozen=True, slots=True)
class PlaneCarrier:
    OriginCm: KJournalVector
    Normal: KJournalVector
    ReferenceAxis: KJournalVector


# cylinder carrier needs an explicit state contract so nested spline and surface records retain their relationships
@MakeDataClass(frozen=True, slots=True)
class CylinderCarrier:
    OriginCm: KJournalVector
    AxisVector: KJournalVector
    MajorAxisCm: KJournalVector


# the face carrier variants need one shared contract so complex journal geometry cannot omit a supported value shape
KFaceCarrier: TypeAlias = BsSurface | PlaneCarrier | CylinderCarrier


# nurbs edge needs an explicit state contract so nested spline and surface records retain their relationships
@MakeDataClass(frozen=True, slots=True)
class NurbsEdge:
    StartVertex: int
    EndVertex: int
    Curve: BsCurve
    Bounds: tuple[float, float] | None = None


# nurbs use needs an explicit state contract so nested spline and surface records retain their relationships
@MakeDataClass(frozen=True, slots=True)
class NurbsUse:
    EdgeIndex: int
    Reversed: bool
    Pcurve: BsCurve | None
    OffsetU: float = 0.0
    OffsetV: float = 0.0


# nurbs face needs an explicit state contract so nested spline and surface records retain their relationships
@MakeDataClass(frozen=True, slots=True)
class NurbsFace:
    Surface: KFaceCarrier
    Uses: tuple[NurbsUse, ...]
    Holes: tuple[tuple[NurbsUse, ...], ...] = ()


# nurbs body needs an explicit state contract so nested spline and surface records retain their relationships
@MakeDataClass(frozen=True, slots=True)
class NurbsBody:
    PointsCm: tuple[KJournalVector, ...]
    Edges: tuple[NurbsEdge, ...]
    Faces: tuple[NurbsFace, ...]
    EntityTag: int = -1
