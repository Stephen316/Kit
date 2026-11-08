# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import cos as Cosine, dist as Distance, hypot as Hypot
from math import isfinite as IsFinite, sin as SineValue, ulp as UnitPlace

from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from convert.geometry.Extrude.Trimmed.TrimOperand import TrimOperand
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.curves.BrepCurves import BrepCurve, CircleCurve, LineCurve
from interchange.brep.topology.BrepTopology import BrepEdge, BrepVertex
from interchange.geometry.models.GeometryCurves import ArcGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# planar lines preserve the source tangent even when world coordinates round their endpoints
def MakeTrimLine(
    CurveId: str, Operand: TrimOperand, FrameValue: Transform, Height: float
) -> tuple[LineCurve, float, SpaceVector]:
    DeltaX = Operand.Finish.x - Operand.Start.x
    DeltaY = Operand.Finish.y - Operand.Start.y
    Length = Hypot(DeltaX, DeltaY)
    Direction = OffsetVector(
        SpaceVector(0.0, 0.0, 0.0), FrameValue.x_axis, DeltaX / Length
    )
    Direction = OffsetVector(Direction, FrameValue.y_axis, DeltaY / Length)
    Start = PlacePrismPoint(FrameValue, Operand.Start, Height)
    return (
        LineCurve(CurveId, Start, Direction),
        Length,
        OffsetVector(Start, Direction, Length),
    )


# curve endpoints and shared topological vertices must agree at physical tolerance
def GetEdgeTol(
    First: BrepVertex,
    Second: BrepVertex,
    Start: SpaceVector,
    Finish: SpaceVector,
    Tolerance: float,
) -> float:
    Actual = ((Start.x, Start.y, Start.z), (Finish.x, Finish.y, Finish.z))
    Shared = tuple(
        (Value.point.x, Value.point.y, Value.point.z) for Value in (First, Second)
    )
    if not all(IsFinite(Value) for Point in (*Actual, *Shared) for Value in Point):
        raise ValueError("Extrude trim edge coordinates exceed floating range")
    Scale = max(abs(Value) for Point in (*Actual, *Shared) for Value in Point)
    Tolerance = max(Tolerance, 8.0 * UnitPlace(Scale))
    if (
        Actual[0] == Actual[1]
        or Shared[0] == Shared[1]
        or any(
            Distance(Endpoint, Vertex) > Tolerance
            for Endpoint, Vertex in zip(Actual, Shared)
        )
    ):
        raise ValueError(
            "Extrude trim edge endpoints lose precision in the spatial frame"
        )
    return Tolerance


# intrinsic curve orientation keeps the stored arc domain positive for either loop sense
def MakeTrimRim(
    Identity: str,
    Operand: TrimOperand,
    FrameValue: Transform,
    Height: float,
    First: BrepVertex,
    Second: BrepVertex,
    Tolerance: float,
) -> tuple[BrepCurve, BrepEdge]:
    CurveId = f"{Identity}-curve"
    Geometry = Operand.Geometry
    if isinstance(Geometry, ArcGeometry):
        Center = PlacePrismPoint(FrameValue, Geometry.center, Height)
        Radius = Geometry.radius
        Curve = CircleCurve(
            CurveId, Center, FrameValue.z_axis, FrameValue.x_axis, Radius
        )
        Lower, Upper = Geometry.start_angle, Geometry.end_angle
        Start, Finish = (
            OffsetVector(
                OffsetVector(Center, FrameValue.x_axis, Radius * Cosine(Angle)),
                FrameValue.y_axis,
                Radius * SineValue(Angle),
            )
            for Angle in (Lower, Upper)
        )
    else:
        Curve, Upper, Finish = MakeTrimLine(CurveId, Operand, FrameValue, Height)
        Start = Curve.origin
        Lower = 0.0
    Accuracy = GetEdgeTol(First, Second, Start, Finish, Tolerance)
    return Curve, BrepEdge(
        Identity, First.id, Second.id, CurveId, Lower, Upper, tolerance=Accuracy
    )
