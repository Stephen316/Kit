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
    ReadSurfaces,
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


# the line profile of a recomputed revolve can retain coedge surface data
def ReadWireTables(
    Cursor: Tokens, CurveCount: int, AllowPcurves: bool
) -> tuple[int, int, tuple[BrepCurve, ...]]:
    Pcurves, Curves = ReadModelCurves(Cursor, "freecad:saved-sketch")
    CurveKinds = (LineCurve,) if AllowPcurves else (LineCurve, CircleCurve)
    if (
        (Pcurves and not AllowPcurves)
        or len(Curves) > CurveCount
        or any(not isinstance(Curve, CurveKinds) for Curve in Curves)
    ):
        raise DecodeFailure("unsupported saved sketch cache curves")
    ZeroTable(Cursor, b"Polygon3D")
    ZeroTable(Cursor, b"PolygonOnTriangulations")
    Surfaces = 0
    if AllowPcurves:
        Surfaces = ReadSurfaces(Cursor)
    else:
        ZeroTable(Cursor, b"Surfaces")
    ZeroTable(Cursor, b"Triangulations")
    return Pcurves, Surfaces, Curves


# exact bounded cache grammar excludes faces and requires independent spatial wire geometry
def ReadSavedWire(
    ShapeData: bytes, CurveCount: int, PointCount: int, *, AllowPcurves: bool = False
) -> SavedWireData:
    Cursor = Tokens(ShapeData)
    ExpectHeader(Cursor)
    Locations = ModelLocations(Cursor)
    LocationLimit = 512 if AllowPcurves else 16
    if len(Locations) > LocationLimit or any(
        abs(LocationScale(Value) - 1.0) > KAngleTolerance for Value in Locations
    ):
        raise DecodeFailure("unsupported saved sketch cache placement")
    Pcurves, Surfaces, Curves = ReadWireTables(Cursor, CurveCount, AllowPcurves)
    Count = ReadCount(Cursor, b"TShapes", 1 + 4 * CurveCount + PointCount)
    Records = ShapeRecords(
        Cursor, Count, len(Curves), Pcurves, Surfaces, len(Locations)
    )
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
