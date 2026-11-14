import math

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
    FormFace,
    FormSurface,
    FormUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot


def SpanKnots(Spans: int) -> tuple[float, ...]:
    return tuple(float(Index) for Index in range(Spans + 1))


def SpanCounts(Spans: int) -> tuple[int, ...]:
    return (3, *([1] * (Spans - 1)), 3)


def PolePlaces(Spans: int) -> list[float]:
    Spread = (
        [0.0] * 4 + [float(Index) for Index in range(1, Spans)] + [float(Spans)] * 4
    )
    return [sum(Spread[Index + 1 : Index + 4]) / 3.0 for Index in range(Spans + 3)]


def FoldCrease(Spans: int) -> BsCurve:
    Poles = tuple((0.0, Place, 0.0) for Place in PolePlaces(Spans))
    return BsCurve(False, 3, 0, SpanKnots(Spans), SpanCounts(Spans), 3, Poles, ())


def FoldTrace(Spans: int, Across: float) -> BsCurve:
    Poles = ((Across, 0.0), (Across, float(Spans)))
    return BsCurve(False, 1, 0, (0.0, float(Spans)), (1, 1), 2, Poles, ())


def FoldSheet(
    Spans: int, RowPairs: list[tuple[KJournalVector, KJournalVector]]
) -> NubsSurface:
    KnotsU = (SplineKnot(0.0, 1), SplineKnot(1.0, 1))
    KnotsV = tuple(
        SplineKnot(KnotValue, Count)
        for KnotValue, Count in zip(SpanKnots(Spans), SpanCounts(Spans))
    )
    Points = tuple(Point for RowValue in RowPairs for Point in RowValue)
    return NubsSurface(1, 3, 0, 0, 0, 0, KnotsU, KnotsV, Points)


def FoldFaces(Angles: tuple[float, ...]) -> tuple[NubsSurface, NubsSurface]:
    Spans = len(Angles) - 3
    Places = PolePlaces(Spans)
    Crease = [(0.0, Place, 0.0) for Place in Places]
    FlatSheet = FoldSheet(Spans, [(Point, (-1.0, Point[1], 0.0)) for Point in Crease])
    Turned = [
        (math.cos(math.radians(Angle)), Place, -math.sin(math.radians(Angle)))
        for Angle, Place in zip(Angles, Places)
    ]
    return FlatSheet, FoldSheet(Spans, list(zip(Turned, Crease)))


def FoldBody(Angles: tuple[float, ...], Splits: tuple[float, ...] = ()) -> FormBody:
    Spans = len(Angles) - 3
    Curve = FoldCrease(Spans)
    Breaks = [0.0, *Splits, float(Spans)]
    Edges = tuple(
        FormEdge(
            Index,
            Index + 1,
            Curve,
            (),
            "unknown",
            Bounds=None if not Splits else (Begin, Finish),
        )
        for Index, (Begin, Finish) in enumerate(zip(Breaks, Breaks[1:]))
    )
    FlatSheet, Turned = FoldFaces(Angles)
    Faces = tuple(
        FormFace(
            FormSurface(Sheet, (), 0),
            tuple(
                FormUse(Index, Sheet is FlatSheet, FoldTrace(Spans, Across))
                for Index in range(len(Edges))
            ),
        )
        for Sheet, Across in ((FlatSheet, 0.0), (Turned, 1.0))
    )
    Points = tuple((0.0, Place, 0.0) for Place in Breaks)
    return FormBody(Points, Edges, Faces, ())
