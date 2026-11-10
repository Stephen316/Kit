# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from math import cos as Cosine, sin as SinValue, tau as FullTurn

from convert.adapters.freecad.EditShape.CylinderRims import (
    IsNearPoint,
    IsParallel,
    KAngleTolerance,
    KPositionTolerance,
)
from convert.adapters.freecad.EditShape.Sketch.WireEdge import EvalWireCurve, SavedEdge
from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
)
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector

# supported cache edges retain exactly the editable finite curve families
KSketchCurve = ArcGeometry | CircleGeometry | LineGeometry


# angular trims require independent positions in the saved sketch frame
def PlaceArcPoint(
    ArcValue: ArcGeometry, FrameValue: Transform, Angle: float
) -> SpaceVector:
    return PlacePrismPoint(
        FrameValue,
        PlaneVector(
            ArcValue.center.x + ArcValue.radius * Cosine(Angle),
            ArcValue.center.y + ArcValue.radius * SinValue(Angle),
        ),
        0.0,
    )


# edge orientation may differ without changing the authored trimmed interval
def IsSameEnds(
    Points: tuple[SpaceVector, SpaceVector], Start: SpaceVector, EndPoint: SpaceVector
) -> bool:
    return (IsNearPoint(Points[0], Start) and IsNearPoint(Points[1], EndPoint)) or (
        IsNearPoint(Points[1], Start) and IsNearPoint(Points[0], EndPoint)
    )


# a line circle or bounded arc must match its complete independent shape cache geometry
def IsSameEdge(
    EdgeValue: SavedEdge,
    Original: KSketchCurve,
    FrameValue: Transform,
    DirectedLines: bool = False,
) -> bool:
    Curve = EdgeValue.Curve
    if isinstance(Original, LineGeometry):
        Start = PlacePrismPoint(FrameValue, Original.start, 0.0)
        EndPoint = PlacePrismPoint(FrameValue, Original.end, 0.0)
        return isinstance(Curve, LineCurve) and (
            (
                IsNearPoint(EdgeValue.Points[0], Start)
                and IsNearPoint(EdgeValue.Points[1], EndPoint)
            )
            if DirectedLines
            else IsSameEnds(EdgeValue.Points, Start, EndPoint)
        )
    if (
        not isinstance(Curve, CircleCurve)
        or abs(Curve.radius - Original.radius) > KPositionTolerance
        or not IsParallel(Curve.axis, FrameValue.z_axis)
        or not IsNearPoint(
            Curve.center, PlacePrismPoint(FrameValue, Original.center, 0.0)
        )
    ):
        return False
    First, LastValue = EdgeValue.Interval
    SpanValue = LastValue - First
    if isinstance(Original, CircleGeometry):
        return abs(SpanValue - FullTurn) <= KAngleTolerance
    if abs(SpanValue - (Original.end_angle - Original.start_angle)) > KAngleTolerance:
        return False
    return IsSameEnds(
        EdgeValue.Points,
        PlaceArcPoint(Original, FrameValue, Original.start_angle),
        PlaceArcPoint(Original, FrameValue, Original.end_angle),
    ) and IsNearPoint(
        EvalWireCurve(Curve, First + SpanValue / 2.0),
        PlaceArcPoint(
            Original, FrameValue, (Original.start_angle + Original.end_angle) / 2.0
        ),
    )
