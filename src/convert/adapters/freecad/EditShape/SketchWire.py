# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.EditShape.CylinderRims import (
    IsFullRim,
    IsNearPoint,
    IsParallel,
    KPositionTolerance,
)
from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from convert.geometry.Opencascade import (
    ApplyLocations,
    DecodeFailure,
    EdgeData,
    ExpectHeader,
    ModelLocations,
    ReadCount,
    ReadModelCurves,
    ReadReference,
    ShapeRecords,
    Tokens,
    VertexData,
    ZeroTable,
)
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.brep.topology.BrepTopology import BrepEdge
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Transform import Transform


# a saved sketch cache can only represent its verified single circular profile
def IsSketchWire(
    ShapeData: bytes, FrameValue: Transform, Profile: CircleGeometry
) -> bool:
    try:
        Cursor = Tokens(ShapeData)
        ExpectHeader(Cursor)
        Locations = ModelLocations(Cursor)
        PcurveCount, Curves = ReadModelCurves(Cursor, "freecad:edit-sketch")
        if PcurveCount or len(Curves) != 1 or len(Locations) > 16:
            return False
        for Table in (
            b"Polygon3D",
            b"PolygonOnTriangulations",
            b"Surfaces",
            b"Triangulations",
        ):
            ZeroTable(Cursor, Table)
        Count = ReadCount(Cursor, b"TShapes", 3)
        if Count != 3:
            return False
        Records = ShapeRecords(Cursor, Count, 1, 0, 0, len(Locations))
        RootRef = ReadReference(Cursor, Count, len(Locations))
        if RootRef is None or Cursor.PeekToken() is not None:
            return False
        Curves, _, Records, RootRef = ApplyLocations(
            Curves, (), Records, RootRef, Locations, "freecad:edit-sketch"
        )
        Wire = Records[RootRef.RecordA]
        if (
            Wire.KindValue != b"Wi"
            or Wire.FlagBits[4] != "1"
            or len(Wire.Children) != 1
        ):
            return False
        EdgeRecord = Records[Wire.Children[0].RecordA]
        EdgeValue = EdgeRecord.GeometryA
        if not isinstance(EdgeValue, EdgeData) or len(EdgeRecord.Children) != 2:
            return False
        First, LastValue = EdgeRecord.Children
        if First.RecordA != LastValue.RecordA or {
            First.Orientation,
            LastValue.Orientation,
        } != {"+", "-"}:
            return False
        Vertex = Records[First.RecordA].GeometryA
        Curve = Curves[EdgeValue.Curve - 1]
        if not isinstance(Vertex, VertexData) or not isinstance(Curve, CircleCurve):
            return False
        Rim = BrepEdge(
            "sketch:rim",
            "sketch:vertex",
            "sketch:vertex",
            Curve.id,
            EdgeValue.FirstValue,
            EdgeValue.LastValue,
        )
        return (
            max(EdgeValue.Tolerance, Vertex.Tolerance) <= KPositionTolerance
            and abs(Curve.radius - Profile.radius) <= KPositionTolerance
            and IsNearPoint(
                Curve.center, PlacePrismPoint(FrameValue, Profile.center, 0.0)
            )
            and IsParallel(Curve.axis, FrameValue.z_axis)
            and IsFullRim(Rim, Curve, Vertex.Point)
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
