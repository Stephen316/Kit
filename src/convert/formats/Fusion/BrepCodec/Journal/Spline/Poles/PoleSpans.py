from fractions import Fraction
from functools import cache as CacheResult
from typing import Mapping as KMapping

from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.FaceNets import (
    KCornerSteps,
    KNetRows,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleMesh import KFaceKey
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KPoleRow,
    MixRows,
)

KFrame = tuple[Fraction, Fraction, Fraction, Fraction, Fraction, Fraction]
KPlace = tuple[Fraction, Fraction]
KArgs = tuple[Fraction, Fraction, Fraction]
KNetTable = KMapping[KFaceKey, KNetRows | None]
KUnitFrame: KFrame = (
    Fraction(1),
    Fraction(0),
    Fraction(0),
    Fraction(1),
    Fraction(0),
    Fraction(0),
)


@CacheResult
def BlossomBasis(Arguments: KArgs) -> tuple[float, ...]:
    Knots = tuple(Fraction(Value) for Value in range(-3, 5))
    Basis = [
        tuple(Fraction(int(RowIndex == Column)) for Column in range(4))
        for RowIndex in range(4)
    ]
    for Level in range(1, 4):
        Fresh = list(Basis)
        for Index in range(3, Level - 1, -1):
            Alpha = (Arguments[Level - 1] - Knots[Index]) / (
                Knots[Index + 4 - Level] - Knots[Index]
            )
            Fresh[Index] = tuple(
                (1 - Alpha) * LowerPart + Alpha * UpperPart
                for LowerPart, UpperPart in zip(Basis[Index - 1], Basis[Index])
            )
        Basis = Fresh
    return tuple(float(Value) for Value in Basis[3])


def NetBlossom(NetRows: KNetRows, ArgsS: KArgs, ArgsT: KArgs) -> KPoleRow:
    WeightS = BlossomBasis(tuple(sorted(ArgsS)))
    WeightT = BlossomBasis(tuple(sorted(ArgsT)))
    return MixRows(
        (WeightT[RowIndex] * WeightS[Column], NetRows[RowIndex][Column])
        for RowIndex in range(4)
        for Column in range(4)
    )


def ApplyFrame(Frame: KFrame, Place: KPlace) -> KPlace:
    return (
        Frame[0] * Place[0] + Frame[1] * Place[1] + Frame[4],
        Frame[2] * Place[0] + Frame[3] * Place[1] + Frame[5],
    )


def ChildFrame(Frame: KFrame, Corner: int) -> KFrame:
    Origin = KCornerSteps[Corner]
    AxisU = [
        2 * (KCornerSteps[(Corner + 1) % 4][Index] - Origin[Index])
        for Index in range(2)
    ]
    AxisV = [
        2 * (KCornerSteps[(Corner - 1) % 4][Index] - Origin[Index])
        for Index in range(2)
    ]
    ShiftU = -(AxisU[0] * Origin[0] + AxisU[1] * Origin[1])
    ShiftV = -(AxisV[0] * Origin[0] + AxisV[1] * Origin[1])
    return (
        AxisU[0] * Frame[0] + AxisU[1] * Frame[2],
        AxisU[0] * Frame[1] + AxisU[1] * Frame[3],
        AxisV[0] * Frame[0] + AxisV[1] * Frame[2],
        AxisV[0] * Frame[1] + AxisV[1] * Frame[3],
        AxisU[0] * Frame[4] + AxisU[1] * Frame[5] + ShiftU,
        AxisV[0] * Frame[4] + AxisV[1] * Frame[5] + ShiftV,
    )


def IsInQuarter(
    Frame: KFrame, LowPlace: KPlace, HighPlace: KPlace, Corner: int
) -> bool:
    Points = [
        ApplyFrame(Frame, (PlaceS, PlaceT))
        for PlaceS in (LowPlace[0], HighPlace[0])
        for PlaceT in (LowPlace[1], HighPlace[1])
    ]
    HalfStep = Fraction(1, 2)
    for AxisIndex in range(2):
        Lowest = HalfStep * KCornerSteps[Corner][AxisIndex]
        Values = [Point[AxisIndex] for Point in Points]
        if min(Values) < Lowest or max(Values) > Lowest + HalfStep:
            return False
    return True


def Descend(
    NetTable: KNetTable,
    FaceKey: KFaceKey,
    Frame: KFrame,
    LowPlace: KPlace,
    HighPlace: KPlace,
) -> tuple[KFrame, KNetRows] | None:
    if FaceKey not in NetTable:
        return None
    NetRows = NetTable[FaceKey]
    if NetRows is not None:
        return (Frame, NetRows)
    for Corner in range(4):
        if IsInQuarter(Frame, LowPlace, HighPlace, Corner):
            Found = Descend(
                NetTable,
                FaceKey + (Corner,),
                ChildFrame(Frame, Corner),
                LowPlace,
                HighPlace,
            )
            if Found is not None:
                return Found
    return None


def CellPlace(
    CellValue: PatchCell, Scale: int, PlaceU: Fraction, PlaceV: Fraction
) -> KPlace:
    for _ in range((-CellValue.Offset[2]) % 4):
        PlaceU, PlaceV = -PlaceV, PlaceU
    return (
        (PlaceU + Fraction(CellValue.Offset[1])) / Scale,
        (PlaceV + Fraction(CellValue.Offset[0])) / Scale,
    )


def SpanBox(
    CellValue: PatchCell, Scale: int, SpanU: KPlace, SpanV: KPlace
) -> tuple[KPlace, KPlace] | None:
    First = CellPlace(CellValue, Scale, SpanU[0], SpanV[0])
    Second = CellPlace(CellValue, Scale, SpanU[1], SpanV[1])
    LowPlace = (
        max(Fraction(0), min(First[0], Second[0])),
        max(Fraction(0), min(First[1], Second[1])),
    )
    HighPlace = (
        min(Fraction(1), max(First[0], Second[0])),
        min(Fraction(1), max(First[1], Second[1])),
    )
    if LowPlace[0] >= HighPlace[0] or LowPlace[1] >= HighPlace[1]:
        return None
    return (LowPlace, HighPlace)


def LocalArgs(
    CellValue: PatchCell, Scale: int, Frame: KFrame, ArgsU: KArgs, ArgsV: KArgs
) -> tuple[KArgs, KArgs]:
    def LocalOf(PlaceU: Fraction, PlaceV: Fraction) -> KPlace:
        return ApplyFrame(Frame, CellPlace(CellValue, Scale, PlaceU, PlaceV))

    FromU = [LocalOf(PlaceU, ArgsV[0]) for PlaceU in ArgsU]
    FromV = [LocalOf(ArgsU[0], PlaceV) for PlaceV in ArgsV]
    UFeedsS = LocalOf(ArgsU[0] + 1, ArgsV[0])[0] != FromU[0][0]
    if UFeedsS:
        return (
            (FromU[0][0], FromU[1][0], FromU[2][0]),
            (FromV[0][1], FromV[1][1], FromV[2][1]),
        )
    return (
        (FromV[0][0], FromV[1][0], FromV[2][0]),
        (FromU[0][1], FromU[1][1], FromU[2][1]),
    )


def SpanRow(
    NetTable: KNetTable,
    Cells: tuple[PatchCell, ...],
    Scale: int,
    Arguments: tuple[KArgs, KArgs],
    Spans: tuple[KPlace, KPlace],
) -> KPoleRow | None:
    for CellValue in Cells:
        BoxValue = SpanBox(CellValue, Scale, Spans[0], Spans[1])
        if BoxValue is None:
            continue
        Found = Descend(
            NetTable, (CellValue.Face,), KUnitFrame, BoxValue[0], BoxValue[1]
        )
        if Found is None:
            continue
        ArgsS, ArgsT = LocalArgs(CellValue, Scale, Found[0], Arguments[0], Arguments[1])
        return NetBlossom(Found[1], ArgsS, ArgsT)
    return None


def PoleRow(
    NetTable: KNetTable,
    Cells: tuple[PatchCell, ...],
    Scale: int,
    FullU: tuple[Fraction, ...],
    FullV: tuple[Fraction, ...],
    PoleSpot: tuple[int, int],
) -> KPoleRow | None:
    RowIndex, Column = PoleSpot
    ArgsU = (FullU[Column + 1], FullU[Column + 2], FullU[Column + 3])
    ArgsV = (FullV[RowIndex + 1], FullV[RowIndex + 2], FullV[RowIndex + 3])
    SpansU = [
        (FullU[Index], FullU[Index + 1])
        for Index in range(Column, Column + 4)
        if FullU[Index] < FullU[Index + 1]
    ]
    SpansV = [
        (FullV[Index], FullV[Index + 1])
        for Index in range(RowIndex, RowIndex + 4)
        if FullV[Index] < FullV[Index + 1]
    ]
    for SpanU in SpansU:
        for SpanV in SpansV:
            Found = SpanRow(NetTable, Cells, Scale, (ArgsU, ArgsV), (SpanU, SpanV))
            if Found is not None:
                return Found
    return None
