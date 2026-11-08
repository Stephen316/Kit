# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.EditShape.CylinderRims import (
    KAngleTolerance,
    KPositionTolerance,
)
from convert.adapters.freecad.EditShape.TrimBind import ReadTrimBinds, TrimBinding
from convert.adapters.freecad.EditShape.TrimGeometry import (
    IsTrimAligned,
    IsTrimFamily,
    IsUnitPair,
    SurfaceHand,
    TrimCurve,
    TrimPoint,
)
from convert.geometry.Opencascade import (
    AssertReachable,
    DecodeFailure,
    EdgeData,
    ExpectHeader,
    FaceData,
    KIdentityLocation,
    LocationScale,
    ModelLocations,
    ProductLocation,
    ReadCount,
    ReadModelCurves,
    ReadModelSurfs,
    ReadReference,
    Reference,
    ShapeRecord,
    ShapeRecords,
    Tokens,
    VectorValue,
    ZeroTable,
)
from convert.geometry.Revolve.SweepVector import CrossVector, DotVector
from interchange.brep.curves.BrepCurves import BrepCurve, CircleCurve, LineCurve
from interchange.brep.surfaces.BrepSurfaces import (
    BrepSurface,
    CylinderSurface,
    PlaneSurface,
)


# raw representation data proves parameter trims discarded by the general decoder
@MakeDataClass(frozen=True, slots=True)
class CylinderRaw:
    Locations: tuple[tuple[float, ...], ...]
    Pcurves: tuple[TrimCurve, ...]
    Curves: tuple[BrepCurve, ...]
    Surfaces: tuple[BrepSurface, ...]
    Records: dict[int, ShapeRecord]
    Bindings: dict[int, tuple[TrimBinding, ...]]
    RootRef: Reference

    # the identity index and located cap references use the same composition order
    def Placement(
        self, Index: int, Parent: tuple[float, ...] = KIdentityLocation
    ) -> tuple[float, ...]:
        return ProductLocation(self.Locations[Index], Parent)


# a narrow trim reader avoids accepting arbitrary unverified curve families
def ReadPcurves(Cursor: Tokens) -> tuple[TrimCurve, ...]:
    Count = ReadCount(Cursor, b"Curve2ds", 6)
    Result: list[TrimCurve] = []
    for _ in range(Count):
        KindValue = Cursor.ReadInteger(1, 2)
        Center = (Cursor.ReadNumber(), Cursor.ReadNumber())
        Direction = (Cursor.ReadNumber(), Cursor.ReadNumber())
        if not IsUnitPair(Direction):
            raise DecodeFailure("invalid extrusion pcurve direction")
        if KindValue == 1:
            Result.append(TrimCurve(Center, Direction))
            continue
        SideVector = (Cursor.ReadNumber(), Cursor.ReadNumber())
        Radius = Cursor.ReadNumber()
        if (
            not IsUnitPair(SideVector)
            or abs(Direction[0] * SideVector[0] + Direction[1] * SideVector[1])
            > KAngleTolerance
            or Radius <= 0.0
        ):
            raise DecodeFailure("invalid extrusion pcurve circle frame")
        Result.append(TrimCurve(Center, Direction, SideVector, Radius))
    return tuple(Result)


# the shared decoder exposes circle axes but discards the stored second basis vector
def CheckCurveAxes(Cursor: Tokens) -> None:
    Count = ReadCount(Cursor, b"Curves", 3)
    for _ in range(Count):
        KindValue = Cursor.ReadInteger(1, 2)
        _ = VectorValue(Cursor)
        AxisValue = VectorValue(Cursor)
        if KindValue == 2:
            First = VectorValue(Cursor)
            Second = VectorValue(Cursor)
            _ = Cursor.ReadNumber()
            if DotVector(CrossVector(AxisValue, First), Second) < 1.0 - KAngleTolerance:
                raise DecodeFailure("unsupported extrusion circle handedness")


# topology is parsed with the existing decoder before extracting the exact edge representations
def ReadCylinderRaw(ShapeData: bytes) -> CylinderRaw:
    Cursor = Tokens(ShapeData)
    ExpectHeader(Cursor)
    Locations = ModelLocations(Cursor)
    if len(Locations) > 16 or any(
        abs(LocationScale(Value) - 1.0) > KAngleTolerance for Value in Locations
    ):
        raise DecodeFailure("unsupported extrusion locations")
    ModelStart = Cursor.LastEnd
    Pcurves = ReadPcurves(Cursor)
    CheckCurveAxes(Cursor)
    Cursor = Tokens(ShapeData[ModelStart:])
    _, Curves = ReadModelCurves(Cursor, "freecad:edit-cylinder-raw")
    ZeroTable(Cursor, b"Polygon3D")
    ZeroTable(Cursor, b"PolygonOnTriangulations")
    Surfaces = ReadModelSurfs(Cursor, "freecad:edit-cylinder-raw")
    ZeroTable(Cursor, b"Triangulations")
    Count = ReadCount(Cursor, b"TShapes", 13)
    Records = ShapeRecords(
        Cursor, Count, len(Curves), len(Pcurves), len(Surfaces), len(Locations)
    )
    RootRef = ReadReference(Cursor, Count, len(Locations))
    if RootRef is None or Records[RootRef.RecordA].KindValue != b"So":
        raise DecodeFailure("extrusion root must be a single solid")
    AssertReachable(
        RootRef.RecordA,
        {
            Index: tuple(Child.RecordA for Child in Value.Children)
            for Index, Value in Records.items()
        },
        {Index: Value.KindValue for Index, Value in Records.items()},
    )
    EdgeRecords = [
        Index for Index, Value in Records.items() if Value.KindValue == b"Ed"
    ]
    EdgeBlocks = [
        Value for Value in b"\n".join(ShapeData.splitlines()).split(b"\nEd\n")[1:]
    ]
    if len(EdgeRecords) != len(EdgeBlocks):
        raise DecodeFailure("cannot locate saved extrusion edge trims")
    Bindings = {
        Index: ReadTrimBinds(Value, len(Pcurves), len(Surfaces), len(Locations))
        for Index, Value in zip(EdgeRecords, EdgeBlocks, strict=True)
    }
    return CylinderRaw(
        (KIdentityLocation, *Locations),
        Pcurves,
        Curves,
        Surfaces,
        Records,
        Bindings,
        RootRef,
    )


# axis parity is recovered before record placement so rotated locations remain valid
def ReadFaceHands(RawValue: CylinderRaw) -> dict[int, int]:
    return {
        Index: SurfaceHand(Value) for Index, Value in enumerate(RawValue.Surfaces, 1)
    }


# independently established geometry and trim intervals must agree in edge coordinates
def IsEdgeTrimValid(
    RawValue: CylinderRaw, EdgeValue: EdgeData, Binding: TrimBinding
) -> bool:
    Surface = RawValue.Surfaces[Binding.SurfaceId - 1]
    Curve = RawValue.Curves[EdgeValue.Curve - 1]
    if (
        not isinstance(Surface, (CylinderSurface, PlaneSurface))
        or not isinstance(Curve, (CircleCurve, LineCurve))
        or abs(Binding.Lower - EdgeValue.FirstValue) > KAngleTolerance
        or abs(Binding.Upper - EdgeValue.LastValue) > KAngleTolerance
    ):
        return False
    Trims = tuple(RawValue.Pcurves[Index - 1] for Index in Binding.CurveIds)
    return IsTrimFamily(Surface, Curve, Trims) and all(
        IsTrimAligned(
            Value,
            Surface,
            Curve,
            RawValue.Locations[Binding.Placement],
            RawValue.Locations[EdgeValue.KLocation],
            Binding.Lower,
            Binding.Upper,
        )
        for Value in Trims
    )


# a matching surface location is required even when native saves reuse cap records
def BoundTrimIndex(
    RawValue: CylinderRaw,
    EdgeRef: Reference,
    FaceValue: FaceData,
    FacePlace: tuple[float, ...],
    WirePlace: tuple[float, ...],
) -> int | None:
    EdgePlace = RawValue.Placement(EdgeRef.KLocation, WirePlace)
    SurfacePlace = RawValue.Placement(FaceValue.KLocation, FacePlace)
    Matches: list[int] = []
    for Index, Binding in enumerate(RawValue.Bindings[EdgeRef.RecordA]):
        if Binding.SurfaceId != FaceValue.Surface:
            continue
        BoundPlace = RawValue.Placement(Binding.Placement, EdgePlace)
        if all(
            abs(First - Second)
            <= (KPositionTolerance if Index % 4 == 3 else KAngleTolerance)
            for Index, (First, Second) in enumerate(
                zip(BoundPlace, SurfacePlace, strict=True)
            )
        ):
            Matches.append(Index)
    if len(Matches) > 1:
        raise DecodeFailure("extrusion trim surface binding is ambiguous")
    if not Matches and isinstance(
        RawValue.Surfaces[FaceValue.Surface - 1], CylinderSurface
    ):
        raise DecodeFailure("missing cylindrical trim")
    return Matches[0] if Matches else None


# both oriented seam pcurves must connect to the matching corners of the wrap
def HasTrimLoop(
    RawValue: CylinderRaw, EdgeUses: list[tuple[Reference, TrimBinding]]
) -> bool:
    Starts: list[tuple[float, float]] = []
    EndValues: list[tuple[float, float]] = []
    for EdgeRef, Binding in EdgeUses:
        Reversed = EdgeRef.Orientation == "-"
        CurveId = Binding.CurveIds[-1 if Reversed else 0]
        Curve = RawValue.Pcurves[CurveId - 1]
        Lower = TrimPoint(Curve, Binding.Lower)
        Upper = TrimPoint(Curve, Binding.Upper)
        Starts.append(Upper if Reversed else Lower)
        EndValues.append(Lower if Reversed else Upper)
    return len(EdgeUses) == 4 and all(
        sum(
            abs(Start[0] - EndPoint[0]) <= KAngleTolerance
            and abs(Start[1] - EndPoint[1]) <= KPositionTolerance
            for EndPoint in EndValues
        )
        == 1
        for Start in Starts
    )


# every stored pcurve must belong to the displayed side or a mathematically proved cap
def HasCylTrims(RawValue: CylinderRaw) -> bool:
    RootRef = RawValue.RootRef
    (ShellRef,) = RawValue.Records[RootRef.RecordA].Children
    ShellPlace = RawValue.Placement(
        ShellRef.KLocation, RawValue.Locations[RootRef.KLocation]
    )
    UsedBindings: set[tuple[int, int]] = set()
    for FaceRef in RawValue.Records[ShellRef.RecordA].Children:
        FaceRecord = RawValue.Records[FaceRef.RecordA]
        FaceValue = FaceRecord.GeometryA
        if not isinstance(FaceValue, FaceData):
            return False
        FacePlace = RawValue.Placement(FaceRef.KLocation, ShellPlace)
        (WireRef,) = FaceRecord.Children
        WirePlace = RawValue.Placement(WireRef.KLocation, FacePlace)
        SideUses: list[tuple[Reference, TrimBinding]] = []
        IsSide = isinstance(RawValue.Surfaces[FaceValue.Surface - 1], CylinderSurface)
        for EdgeRef in RawValue.Records[WireRef.RecordA].Children:
            EdgeValue = RawValue.Records[EdgeRef.RecordA].GeometryA
            Index = BoundTrimIndex(RawValue, EdgeRef, FaceValue, FacePlace, WirePlace)
            if Index is None:
                continue
            Binding = RawValue.Bindings[EdgeRef.RecordA][Index]
            if not isinstance(EdgeValue, EdgeData) or not IsEdgeTrimValid(
                RawValue, EdgeValue, Binding
            ):
                return False
            UsedBindings.add((EdgeRef.RecordA, Index))
            if IsSide:
                SideUses.append((EdgeRef, Binding))
        if IsSide and (
            WireRef.Orientation != "+" or not HasTrimLoop(RawValue, SideUses)
        ):
            return False
    return len(UsedBindings) == sum(len(Value) for Value in RawValue.Bindings.values())
