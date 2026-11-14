from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsCurve import (
    CheckBsCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsSurface import (
    CheckBsSurface,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.PoleCount import PoleCount


def FullKnots(
    Knots: tuple[float, ...], Multiplicity: tuple[int, ...]
) -> tuple[float, ...]:
    Expanded = tuple(
        KnotValue
        for KnotValue, Multiple in zip(Knots, Multiplicity, strict=True)
        for _ in range(Multiple)
    )
    return (Expanded[0], *Expanded, Expanded[-1])


def DeBoorPoint(
    Degree: int,
    KnotVector: tuple[float, ...],
    Points: tuple[tuple[float, ...], ...],
    Parameter: float,
) -> tuple[float, ...]:
    Count = len(Points)
    if not KnotVector[Degree] - 1e-12 <= Parameter <= KnotVector[Count] + 1e-12:
        raise ValueError("Fusion B-spline parameter lies outside its domain")
    SpanIndex = Degree
    while SpanIndex < Count - 1 and KnotVector[SpanIndex + 1] <= Parameter:
        SpanIndex += 1
    Pyramid = [Points[SpanIndex - Degree + Offset] for Offset in range(Degree + 1)]
    for Level in range(1, Degree + 1):
        for Offset in range(Degree, Level - 1, -1):
            Index = SpanIndex - Degree + Offset
            Width = KnotVector[Index + Degree + 1 - Level] - KnotVector[Index]
            Alpha = 0.0 if Width == 0.0 else (Parameter - KnotVector[Index]) / Width
            Pyramid[Offset] = tuple(
                (1.0 - Alpha) * Former + Alpha * Latter
                for Former, Latter in zip(Pyramid[Offset - 1], Pyramid[Offset])
            )
    return Pyramid[Degree]


def Homogeneous(
    Poles: tuple[tuple[float, ...], ...], Weights: tuple[float, ...]
) -> tuple[tuple[float, ...], ...]:
    if not Weights:
        return tuple((*Point, 1.0) for Point in Poles)
    return tuple(
        (*(Number * Weight for Number in Point), Weight)
        for Point, Weight in zip(Poles, Weights, strict=True)
    )


def PointOnCurve(Curve: BsCurve, Parameter: float) -> tuple[float, ...]:
    CheckBsCurve(Curve, Curve.Dimension)
    KnotVector = FullKnots(Curve.Knots, Curve.Multiplicity)
    Point = DeBoorPoint(
        Curve.Degree, KnotVector, Homogeneous(Curve.Poles, Curve.Weights), Parameter
    )
    return tuple(Number / Point[-1] for Number in Point[:-1])


def PointOnSurface(
    Surface: BsSurface, UParameter: float, VParameter: float
) -> tuple[float, ...]:
    CheckBsSurface(Surface)
    UCount = PoleCount(Surface.UDegree, Surface.UMultiplicity)
    Lifted = Homogeneous(Surface.Poles, Surface.Weights)
    UVector = FullKnots(Surface.UKnots, Surface.UMultiplicity)
    RowPoints = tuple(
        DeBoorPoint(
            Surface.UDegree, UVector, Lifted[Start : Start + UCount], UParameter
        )
        for Start in range(0, len(Lifted), UCount)
    )
    VVector = FullKnots(Surface.VKnots, Surface.VMultiplicity)
    Point = DeBoorPoint(Surface.VDegree, VVector, RowPoints, VParameter)
    return tuple(Number / Point[-1] for Number in Point[:-1])
