# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass
from math import cos as Cosine, sin as SinValue, tau as FullTurn

from convert.adapters.freecad.EditShape.CylinderRims import (
    IsNearPoint,
    KAngleTolerance,
    KPositionTolerance,
)
from convert.adapters.freecad.EditShape.Sketch.SavedWireData import SavedWireData
from convert.geometry.Opencascade import DecodeFailure, EdgeData, Reference, VertexData
from convert.geometry.Revolve.SweepVector import CrossVector, OffsetVector
from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve
from interchange.geometry.models.VectorSpace import SpaceVector


# bounded analytic edge data retains its trim and oriented vertex identities
@MakeDataClass(frozen=True, slots=True)
class SavedEdge:
    Curve: LineCurve | CircleCurve
    Interval: tuple[float, float]
    VertexIds: tuple[int, int]
    Points: tuple[SpaceVector, SpaceVector]


# analytic support evaluation independently qualifies all trimmed edge vertices
def EvalWireCurve(Curve: LineCurve | CircleCurve, Value: float) -> SpaceVector:
    if isinstance(Curve, LineCurve):
        return OffsetVector(Curve.origin, Curve.direction, Value)
    Tangent = CrossVector(Curve.axis, Curve.reference_direction)
    Along = OffsetVector(
        Curve.center, Curve.reference_direction, Curve.radius * Cosine(Value)
    )
    return OffsetVector(Along, Tangent, Curve.radius * SinValue(Value))


# every edge must use one analytic curve and the same bounded topology vertices
def ReadSavedEdge(DataValue: SavedWireData, EdgeRef: Reference) -> SavedEdge:
    Record = DataValue.Records[EdgeRef.RecordA]
    Geometry = Record.GeometryA
    if (
        Record.KindValue != b"Ed"
        or not isinstance(Geometry, EdgeData)
        or not 0 <= Geometry.Tolerance <= KPositionTolerance
        or Geometry.FirstValue >= Geometry.LastValue
        or len(Record.Children) != 2
        or {Child.Orientation for Child in Record.Children} != {"+", "-"}
        or EdgeRef.Orientation not in {"+", "-"}
        or not 1 <= Geometry.Curve <= len(DataValue.Curves)
    ):
        raise DecodeFailure("invalid saved sketch edge")
    Curve = DataValue.Curves[Geometry.Curve - 1]
    if not isinstance(Curve, (LineCurve, CircleCurve)):
        raise DecodeFailure("invalid saved sketch edge support")
    Interval = (Geometry.FirstValue, Geometry.LastValue)
    VertexIds = tuple(
        Child.RecordA for Child in sorted(Record.Children, key=VertexOrder)
    )
    IsFull = (
        isinstance(Curve, CircleCurve)
        and abs(Interval[1] - Interval[0] - FullTurn) <= KAngleTolerance
    )
    if IsFull != (VertexIds[0] == VertexIds[1]):
        raise DecodeFailure("invalid saved sketch edge closure")
    Points = tuple(EvalWireCurve(Curve, Value) for Value in Interval)
    for Identity, Expected in zip(VertexIds, Points, strict=True):
        Vertex = DataValue.Records[Identity]
        if (
            not isinstance(Vertex.GeometryA, VertexData)
            or Vertex.Children
            or not 0 <= Vertex.GeometryA.Tolerance <= KPositionTolerance
            or not IsNearPoint(Vertex.GeometryA.Point, Expected)
        ):
            raise DecodeFailure("invalid saved sketch edge vertex")
    StartId, EndId = VertexIds if EdgeRef.Orientation == "+" else VertexIds[::-1]
    return SavedEdge(Curve, Interval, (StartId, EndId), (Points[0], Points[1]))


# the parameter order is independent of the containing wire orientation
def VertexOrder(Value: Reference) -> str:
    return Value.Orientation
