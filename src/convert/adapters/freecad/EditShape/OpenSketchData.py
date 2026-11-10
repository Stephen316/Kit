# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.EditShape.CylinderRims import KAngleTolerance
from convert.geometry.Opencascade import (
    ApplyLocations,
    AssertReachable,
    DecodeFailure,
    ExpectHeader,
    LocationScale,
    ModelLocations,
    ReadCount,
    ReadModelCurves,
    ReadReference,
    ShapeRecord,
    ShapeRecords,
    Tokens,
    ZeroTable,
)
from interchange.brep.curves.BrepCurves import LineCurve


# saved native open sketches retain a located compound rather than a solid model
@MakeDataClass(frozen=True, slots=True)
class OpenShapeData:
    Curve: LineCurve
    Records: dict[int, ShapeRecord]
    RootRecord: int


# bounded analytic parsing retains both the wire and independent point occurrences
def ReadOpenShape(ShapeData: bytes, PointCount: int) -> OpenShapeData:
    Cursor = Tokens(ShapeData)
    ExpectHeader(Cursor)
    Locations = ModelLocations(Cursor)
    if len(Locations) > 16 or any(
        abs(LocationScale(Value) - 1.0) > KAngleTolerance for Value in Locations
    ):
        raise DecodeFailure("unsupported independent sketch placement")
    PcurveCount, Curves = ReadModelCurves(Cursor, "freecad:open-sketch")
    if PcurveCount or len(Curves) != 1 or not isinstance(Curves[0], LineCurve):
        raise DecodeFailure("unsupported independent sketch curves")
    for Table in (
        b"Polygon3D",
        b"PolygonOnTriangulations",
        b"Surfaces",
        b"Triangulations",
    ):
        ZeroTable(Cursor, Table)
    Count = ReadCount(Cursor, b"TShapes", 5 + PointCount)
    if Count != 5 + PointCount:
        raise DecodeFailure("unexpected independent sketch topology count")
    Records = ShapeRecords(Cursor, Count, 1, 0, 0, len(Locations))
    RootRef = ReadReference(Cursor, Count, len(Locations))
    if (
        RootRef is None
        or RootRef.RecordA != 1
        or RootRef.Orientation != "+"
        or Cursor.PeekToken() is not None
    ):
        raise DecodeFailure("invalid independent sketch root")
    AssertReachable(
        RootRef.RecordA,
        {
            Index: tuple(Child.RecordA for Child in Value.Children)
            for Index, Value in Records.items()
        },
        {Index: Value.KindValue for Index, Value in Records.items()},
    )
    Curves, _, Records, RootRef = ApplyLocations(
        Curves, (), Records, RootRef, Locations, "freecad:open-sketch"
    )
    if (
        len(Curves) != 1
        or not isinstance(Curves[0], LineCurve)
        or len(Records) != Count
    ):
        raise DecodeFailure("ambiguous located independent sketch topology")
    return OpenShapeData(Curves[0], Records, RootRef.RecordA)
