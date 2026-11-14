from dataclasses import dataclass as MakeDataClass
from math import cos as Cosine, radians as Radians, sin as SineOf

from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    KProfileCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)


@MakeDataClass(frozen=True, slots=True)
class SketchEdge:
    Curve: KProfileCurve
    CurveTag: int
    StartIndex: int | None
    FinishIndex: int | None
    CenterIndex: int | None


@MakeDataClass(frozen=True, slots=True)
class SketchPlan:
    OriginTag: int
    PointsCm: tuple[tuple[float, float], ...]
    PointTags: tuple[int, ...]
    Edges: tuple[SketchEdge, ...]
    NextTag: int
    Ordinal: int = 1
    LiftCm: float = 0.0


def NormalCurve(Curve: KProfileCurve) -> KProfileCurve:
    if isinstance(Curve, ArcCurve) and Curve.SweepDegrees < 0:
        return ArcCurve(
            Curve.CenterMm,
            Curve.RadiusMm,
            Curve.StartDegrees + Curve.SweepDegrees,
            -Curve.SweepDegrees,
        )
    return Curve


def CurveEnds(Curve: KProfileCurve) -> tuple[tuple[float, float], ...]:
    if isinstance(Curve, LineCurve):
        return (Curve.StartMm, Curve.FinishMm)
    if not isinstance(Curve, ArcCurve):
        return ()
    return tuple(
        (
            Curve.CenterMm[0] + Curve.RadiusMm * Cosine(Radians(Angle)),
            Curve.CenterMm[1] + Curve.RadiusMm * SineOf(Radians(Angle)),
        )
        for Angle in (Curve.StartDegrees, Curve.StartDegrees + Curve.SweepDegrees)
    )


def PointSlotMut(Points: list[tuple[float, float]], Point: tuple[float, float]) -> int:
    for Index, Known in enumerate(Points):
        if abs(Known[0] - Point[0]) < 1e-6 and abs(Known[1] - Point[1]) < 1e-6:
            return Index
    Points.append(Point)
    return len(Points) - 1


def PlanSketch(Profile: tuple[KProfileCurve, ...], FirstTag: int) -> SketchPlan:
    Curves = [NormalCurve(Curve) for Curve in Profile]
    Points: list[tuple[float, float]] = []
    Corners = [
        [PointSlotMut(Points, Corner) for Corner in CurveEnds(Curve)]
        for Curve in Curves
    ]
    Centers: list[int | None] = []
    for Curve in Curves:
        if isinstance(Curve, LineCurve):
            Centers.append(None)
            continue
        Points.append(Curve.CenterMm)
        Centers.append(len(Points) - 1)
    CurveTag = FirstTag + 1 + len(Points)
    Edges = tuple(
        SketchEdge(
            Curve,
            CurveTag + Index,
            Corners[Index][0] if Corners[Index] else None,
            Corners[Index][1] if Corners[Index] else None,
            Centers[Index],
        )
        for Index, Curve in enumerate(Curves)
    )
    PointsCm = tuple((Point[0] / 10.0, Point[1] / 10.0) for Point in Points)
    PointTags = tuple(FirstTag + 1 + Index for Index in range(len(Points)))
    return SketchPlan(FirstTag, PointsCm, PointTags, Edges, CurveTag + len(Curves))
