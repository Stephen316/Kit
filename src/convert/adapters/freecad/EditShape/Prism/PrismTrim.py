# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from re import split as SplitValue

from convert.adapters.freecad.EditShape.CylinderRims import KAngleTolerance
from convert.adapters.freecad.EditShape.TrimBind import TrimBinding
from convert.adapters.freecad.EditShape.TrimGeometry import (
    IsTrimAligned,
    IsUnitPair,
    TrimCurve,
)
from convert.geometry.Opencascade import (
    DecodeFailure,
    EdgeData,
    FaceData,
    KIdentityLocation,
    ReadCount,
    ShapeRecord,
    Tokens,
)
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface


# linear planar trims are the only stored edge representations used by kit prisms
def ReadPrismCurves(Cursor: Tokens, Maximum: int) -> tuple[TrimCurve, ...]:
    Count = ReadCount(Cursor, b"Curve2ds", Maximum)
    Curves: list[TrimCurve] = []
    for _ in range(Count):
        _ = Cursor.ReadInteger(1, 1)
        Origin = (Cursor.ReadNumber(), Cursor.ReadNumber())
        AxisValue = (Cursor.ReadNumber(), Cursor.ReadNumber())
        if not IsUnitPair(AxisValue):
            raise DecodeFailure("invalid prism pcurve direction")
        Curves.append(TrimCurve(Origin, AxisValue))
    return tuple(Curves)


# a seed edge carries one three dimensional range and one trim for each adjacent face
def ReadEdgeBinds(
    Block: bytes, TrimCount: int, FaceCount: int, PlaceCount: int
) -> tuple[TrimBinding, ...]:
    Cursor = Tokens(Block)
    _ = Cursor.ReadNumber()
    Cursor.ExpectToken(b"1")
    Cursor.ExpectToken(b"1")
    Cursor.ExpectToken(b"0")
    Cursor.ExpectToken(b"1")
    _ = Cursor.ReadInteger(1)
    _ = Cursor.ReadInteger(0, PlaceCount)
    _ = Cursor.ReadNumber()
    _ = Cursor.ReadNumber()
    Bindings: list[TrimBinding] = []
    for _ in range(2):
        Cursor.ExpectToken(b"2")
        CurveId = Cursor.ReadInteger(1, TrimCount)
        SurfaceId = Cursor.ReadInteger(1, FaceCount)
        Placement = Cursor.ReadInteger(0, PlaceCount)
        Bindings.append(
            TrimBinding(
                (CurveId,),
                SurfaceId,
                Placement,
                Cursor.ReadNumber(),
                Cursor.ReadNumber(),
            )
        )
    Cursor.ExpectToken(b"0")
    return tuple(Bindings)


# exact carrier tables and per edge bindings are checked before topology is accepted
def ReadPrismBinds(
    ShapeData: bytes,
    Records: dict[int, ShapeRecord],
    TrimCount: int,
    FaceCount: int,
    PlaceCount: int = 0,
) -> dict[int, tuple[TrimBinding, ...]]:
    EdgeIds = [Index for Index, Value in Records.items() if Value.KindValue == b"Ed"]
    Blocks = SplitValue(rb"(?<!\S)Ed(?=\s)", ShapeData)[1:]
    if len(EdgeIds) != len(Blocks):
        raise DecodeFailure("cannot locate prism edge trims")
    Result = {
        Index: ReadEdgeBinds(Block, TrimCount, FaceCount, PlaceCount)
        for Index, Block in zip(EdgeIds, Blocks, strict=True)
    }
    UsedIds = [Value.CurveIds[0] for Bindings in Result.values() for Value in Bindings]
    if sorted(UsedIds) != list(range(1, TrimCount + 1)):
        raise DecodeFailure("unreachable or shared prism trim")
    return Result


# each stored linear trim must trace its actual edge on the referenced face plane
def CheckTrimBind(
    Bindings: tuple[TrimBinding, ...],
    Pcurves: tuple[TrimCurve, ...],
    EdgeValue: EdgeData,
    FaceValue: FaceData,
    LineValue: LineCurve,
    Surface: PlaneSurface,
) -> None:
    Matches = [Value for Value in Bindings if Value.SurfaceId == FaceValue.Surface]
    if len(Matches) != 1:
        raise DecodeFailure("missing or ambiguous prism trim face binding")
    Binding = Matches[0]
    if (
        abs(Binding.Lower - EdgeValue.FirstValue) > KAngleTolerance
        or abs(Binding.Upper - EdgeValue.LastValue) > KAngleTolerance
        or not IsTrimAligned(
            Pcurves[Binding.CurveIds[0] - 1],
            Surface,
            LineValue,
            KIdentityLocation,
            KIdentityLocation,
            Binding.Lower,
            Binding.Upper,
        )
    ):
        raise DecodeFailure("prism pcurve disagrees with its analytic edge")
