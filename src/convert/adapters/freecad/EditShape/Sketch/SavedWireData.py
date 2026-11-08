# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.EditShape.CylinderRims import KAngleTolerance
from convert.geometry.Opencascade import (
    ApplyLocations,
    AssertReachable,
    DecodeFailure,
    EdgeData,
    ExpectHeader,
    LocationScale,
    ModelLocations,
    ReadCount,
    ReadModelCurves,
    ReadReference,
    Reference,
    ShapeRecord,
    ShapeRecords,
    Tokens,
    ZeroTable,
)
from interchange.brep.curves.BrepCurves import BrepCurve, CircleCurve, LineCurve


# the qualified topology holds only analytic wire curves and point vertices
@MakeDataClass(frozen=True, slots=True)
class SavedWireData:
    Curves: tuple[BrepCurve, ...]
    Records: dict[int, ShapeRecord]
    RootRef: Reference


# exact bounded cache grammar excludes faces and unused hidden geometry records
def ReadSavedWire(ShapeData: bytes, CurveCount: int, PointCount: int) -> SavedWireData:
    Cursor = Tokens(ShapeData)
    ExpectHeader(Cursor)
    Locations = ModelLocations(Cursor)
    if len(Locations) > 16 or any(
        abs(LocationScale(Value) - 1.0) > KAngleTolerance for Value in Locations
    ):
        raise DecodeFailure("unsupported saved sketch cache placement")
    Pcurves, Curves = ReadModelCurves(Cursor, "freecad:saved-sketch")
    if (
        Pcurves
        or len(Curves) > CurveCount
        or any(not isinstance(Curve, (LineCurve, CircleCurve)) for Curve in Curves)
    ):
        raise DecodeFailure("unsupported saved sketch cache curves")
    for Table in (
        b"Polygon3D",
        b"PolygonOnTriangulations",
        b"Surfaces",
        b"Triangulations",
    ):
        ZeroTable(Cursor, Table)
    Count = ReadCount(Cursor, b"TShapes", 1 + 4 * CurveCount + PointCount)
    Records = ShapeRecords(Cursor, Count, len(Curves), 0, 0, len(Locations))
    RootRef = ReadReference(Cursor, Count, len(Locations))
    if (
        RootRef is None
        or RootRef.RecordA != 1
        or RootRef.Orientation != "+"
        or Cursor.PeekToken() is not None
    ):
        raise DecodeFailure("invalid saved sketch cache root")
    Kinds = {Identity: Value.KindValue for Identity, Value in Records.items()}
    if set(Kinds.values()) - {b"Co", b"Wi", b"Ed", b"Ve"} or {
        Value.GeometryA.Curve
        for Value in Records.values()
        if isinstance(Value.GeometryA, EdgeData)
    } != set(range(1, len(Curves) + 1)):
        raise DecodeFailure("unexpected topology or unused saved sketch cache curves")
    AssertReachable(
        RootRef.RecordA,
        {
            Identity: tuple(Child.RecordA for Child in Value.Children)
            for Identity, Value in Records.items()
        },
        Kinds,
    )
    Curves, _, Records, RootRef = ApplyLocations(
        Curves, (), Records, RootRef, Locations, "freecad:saved-sketch"
    )
    return SavedWireData(Curves, Records, RootRef)
