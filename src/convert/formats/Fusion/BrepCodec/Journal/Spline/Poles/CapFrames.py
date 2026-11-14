from collections import Counter as CountValues
from dataclasses import dataclass as MakeDataClass
from fractions import Fraction
from typing import Iterable as KIterable, Mapping as KMapping

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import KCapKey
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapPlaces import (
    KPolePlace,
    BaseMask,
    CapSpacing,
    CornerGroups,
    CornerUse,
    FacePlan,
    OwnLists,
    PlaceKey,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleKnots import KEndCount
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KPoleRow,
    MixRows,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleSpans import (
    KNetTable,
    PoleRow,
)

KMixRow = dict[int, Fraction]
KKnotList = tuple[Fraction, ...]


@MakeDataClass(frozen=True, slots=True)
class CapFrame:
    Region: int
    Vertex: int
    Uses: tuple[CornerUse, ...]
    BaseU: KKnotList
    BaseV: KKnotList
    Keys: KMapping[KPolePlace, KCapKey]
    MixU: tuple[KMixRow, ...]
    MixV: tuple[KMixRow, ...]
    Places: frozenset[KPolePlace]


def MixWeights(Parts: KIterable[tuple[Fraction, KMixRow]]) -> KMixRow:
    Total: KMixRow = {}
    for Scalar, Weights in Parts:
        for Index, Value in Weights.items():
            Total[Index] = Total.get(Index, Fraction(0)) + Scalar * Value
    return {Index: Value for Index, Value in Total.items() if Value != 0}


def InsertOnce(
    Weights: list[KMixRow], KnotList: list[Fraction], Value: Fraction
) -> list[KMixRow]:
    SpotIndex = max(Index for Index, Entry in enumerate(KnotList) if Entry <= Value)
    Found: list[KMixRow] = []
    for Index in range(len(Weights) + 1):
        if Index <= SpotIndex - KEndCount:
            Found.append(Weights[Index])
        elif Index <= SpotIndex:
            Lower, Upper = KnotList[Index], KnotList[Index + KEndCount]
            Ratio = (Value - Lower) / (Upper - Lower)
            Parts = ((Ratio, Weights[Index]), (1 - Ratio, Weights[Index - 1]))
            Found.append(MixWeights(Parts))
        else:
            Found.append(Weights[Index - 1])
    return Found


def InsertWeights(BaseList: KKnotList, FullList: KKnotList) -> tuple[KMixRow, ...]:
    Weights: list[KMixRow] = [
        {Index: Fraction(1)} for Index in range(len(BaseList) - KEndCount - 1)
    ]
    Current = list(BaseList)
    Extra = CountValues(FullList) - CountValues(BaseList)
    for Value in sorted(Extra.elements()):
        Weights = InsertOnce(Weights, Current, Value)
        Current = sorted(Current + [Value])
    if tuple(Current) != FullList:
        raise ValueError("Fusion Form cap frames found own knots off their face")
    return tuple(Weights)


def MixedPlaces(
    KeyTable: KMapping[KPolePlace, KCapKey],
    MixesU: tuple[KMixRow, ...],
    MixesV: tuple[KMixRow, ...],
) -> frozenset[KPolePlace]:
    KeyRows = {Place[0] for Place in KeyTable}
    KeyColumns = {Place[1] for Place in KeyTable}
    return frozenset(
        (RowIndex, Column)
        for RowIndex, RowMix in enumerate(MixesV)
        if KeyRows.intersection(RowMix)
        for Column, ColumnMix in enumerate(MixesU)
        if KeyColumns.intersection(ColumnMix)
        and any((Inner, Outer) in KeyTable for Inner in RowMix for Outer in ColumnMix)
    )


def OneFrame(
    Graph: CageGraph,
    PlanValue: FacePlan,
    Scale: int,
    Context: tuple[int, list[CornerUse], dict[int, int]],
) -> CapFrame:
    Vertex, UseList, Levels = Context
    BaseU, BaseV = OwnLists(Graph, PlanValue, Scale, (UseList, Levels))
    MaskSet = BaseMask((BaseU, BaseV), UseList, CapSpacing(Scale, Levels[Vertex]))
    KeyTable = {
        Place: PlaceKey((BaseU, BaseV), Place, UseList) for Place in sorted(MaskSet)
    }
    MixesU = InsertWeights(BaseU, PlanValue.FullU)
    MixesV = InsertWeights(BaseV, PlanValue.FullV)
    return CapFrame(
        PlanValue.Region,
        Vertex,
        tuple(UseList),
        BaseU,
        BaseV,
        KeyTable,
        MixesU,
        MixesV,
        MixedPlaces(KeyTable, MixesU, MixesV),
    )


def RegionFrames(
    Graph: CageGraph, PlanValue: FacePlan, Scale: int, Levels: KMapping[int, int]
) -> tuple[CapFrame, ...]:
    return tuple(
        OneFrame(Graph, PlanValue, Scale, (Vertex, UseList, dict(Levels)))
        for (Vertex, _, _), UseList in CornerGroups(
            Graph, PlanValue, Scale, Levels
        ).items()
    )


def BaseRow(
    Frame: CapFrame,
    Answers: KMapping[KCapKey, KPoleRow],
    Context: tuple[KNetTable, FacePlan, int],
    Place: KPolePlace,
) -> KPoleRow:
    NetTable, PlanValue, Scale = Context
    if Place in Frame.Keys:
        Answer = Answers.get(Frame.Keys[Place])
        if Answer is None:
            raise ValueError("Fusion Form cap hook left a cap pole without a row")
        return Answer
    RowValue = PoleRow(
        NetTable, PlanValue.Cells, Scale, Frame.BaseU, Frame.BaseV, Place
    )
    if RowValue is None:
        raise ValueError("Fusion Form cap frame found a pole with no polynomial span")
    return RowValue


def FrameRows(
    Frame: CapFrame,
    Answers: KMapping[KCapKey, KPoleRow],
    Context: tuple[KNetTable, FacePlan, int],
) -> dict[KPolePlace, KPoleRow]:
    Cache: dict[KPolePlace, KPoleRow] = {}
    Found: dict[KPolePlace, KPoleRow] = {}
    for RowIndex, Column in sorted(Frame.Places):
        Parts: list[tuple[float, KPoleRow]] = []
        for Inner, WeightV in Frame.MixV[RowIndex].items():
            for Outer, WeightU in Frame.MixU[Column].items():
                if (Inner, Outer) not in Cache:
                    Cache[(Inner, Outer)] = BaseRow(
                        Frame, Answers, Context, (Inner, Outer)
                    )
                Parts.append((float(WeightV * WeightU), Cache[(Inner, Outer)]))
        Found[(RowIndex, Column)] = MixRows(Parts)
    return Found
