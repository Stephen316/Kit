# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.adapters.freecad.EditShape.CylinderRims import (
    IsNearPoint,
    KPositionTolerance,
)
from convert.adapters.freecad.EditShape.CylinderShape import KMaxCylinderBytes
from convert.adapters.freecad.EditShape.OpenSketchData import (
    OpenShapeData,
    ReadOpenShape,
)
from convert.adapters.freecad.EditShape.OpenSketchGeom import ReadOpenGeom
from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from convert.geometry.Opencascade import (
    DecodeFailure,
    EdgeData,
    ShapeRecord,
    VertexData,
)
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# independent sketch caches cannot introduce extra or moved analytic point geometry
def HasOpenPoints(
    Records: tuple[ShapeRecord, ...], Points: tuple[SpaceVector, ...]
) -> bool:
    Remaining = list(Points)
    for Record in Records:
        Vertex = Record.GeometryA
        if not isinstance(Vertex, VertexData) or Vertex.Tolerance > KPositionTolerance:
            return False
        Match = next(
            (
                Index
                for Index, Value in enumerate(Remaining)
                if IsNearPoint(Value, Vertex.Point)
            ),
            None,
        )
        if Match is None:
            return False
        _ = Remaining.pop(Match)
    return not Remaining


# a cache wire must contain exactly the expected finite segment in its saved frame
def HasOpenSegment(
    ShapeValue: OpenShapeData,
    WireValue: ShapeRecord,
    Start: SpaceVector,
    EndPoint: SpaceVector,
) -> bool:
    if (
        WireValue.FlagBits[4] != "0"
        or len(WireValue.Children) != 1
        or WireValue.Children[0].Orientation not in {"+", "-"}
    ):
        return False
    EdgeValue = ShapeValue.Records[WireValue.Children[0].RecordA]
    Geometry = EdgeValue.GeometryA
    if (
        not isinstance(Geometry, EdgeData)
        or Geometry.Tolerance > KPositionTolerance
        or Geometry.FirstValue >= Geometry.LastValue
        or len(EdgeValue.Children) != 2
        or {Value.Orientation for Value in EdgeValue.Children} != {"+", "-"}
        or EdgeValue.Children[0].RecordA == EdgeValue.Children[1].RecordA
    ):
        return False
    Curve = ShapeValue.Curve
    Limits = tuple(
        OffsetVector(Curve.origin, Curve.direction, Value)
        for Value in (Geometry.FirstValue, Geometry.LastValue)
    )
    if not (
        (IsNearPoint(Limits[0], Start) and IsNearPoint(Limits[1], EndPoint))
        or (IsNearPoint(Limits[1], Start) and IsNearPoint(Limits[0], EndPoint))
    ):
        return False
    for Child in EdgeValue.Children:
        Vertex = ShapeValue.Records[Child.RecordA].GeometryA
        Expected = Limits[0 if Child.Orientation == "+" else 1]
        if (
            not isinstance(Vertex, VertexData)
            or Vertex.Tolerance > KPositionTolerance
            or not IsNearPoint(Vertex.Point, Expected)
        ):
            return False
    return True


# only the original open wire and separate point multiset can round trip as this sketch
def IsOpenSketch(ShapeData: bytes, SketchValue: Sketch, FrameValue: Transform) -> bool:
    if not ShapeData or len(ShapeData) > KMaxCylinderBytes:
        return False

    Original = ReadOpenGeom(SketchValue)
    if Original is None:
        return False
    Segment, Points = Original
    try:
        ShapeValue = ReadOpenShape(ShapeData, len(Points))
        RootValue = ShapeValue.Records[ShapeValue.RootRecord]
        if RootValue.KindValue != b"Co" or any(
            Value.Orientation != "+" for Value in RootValue.Children
        ):
            return False
        Children = tuple(
            ShapeValue.Records[Value.RecordA] for Value in RootValue.Children
        )
        Wires = tuple(Value for Value in Children if Value.KindValue == b"Wi")
        Vertices = tuple(Value for Value in Children if Value.KindValue == b"Ve")
        return (
            len(Wires) == 1
            and len(Vertices) == len(Points)
            and len(Children) == 1 + len(Vertices)
            and HasOpenSegment(
                ShapeValue,
                Wires[0],
                PlacePrismPoint(FrameValue, Segment.start, 0.0),
                PlacePrismPoint(FrameValue, Segment.end, 0.0),
            )
            and HasOpenPoints(
                Vertices,
                tuple(PlacePrismPoint(FrameValue, Value, 0.0) for Value in Points),
            )
        )
    except (
        DecodeFailure,
        IndexError,
        KeyError,
        TypeError,
        ValueError,
        OverflowError,
        RecursionError,
    ):
        return False


# readback imports this explicit name to distinguish cache proof from source qualification
IsOpenSketchCache = IsOpenSketch
