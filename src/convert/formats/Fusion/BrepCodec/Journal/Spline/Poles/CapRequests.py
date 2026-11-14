from fractions import Fraction
from typing import Mapping as KMapping

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapFrames import CapFrame
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import (
    KCapKey,
    KPlaceKey,
    CapInput,
    CapSector,
    SpokeKey,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapPlaces import (
    KReachSpans,
    AxisIndices,
    CapSpacing,
    CornerUse,
    FacePlan,
    SectorKnots,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleLimit import LimitRow
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleMesh import PoleMesh
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import KPoleRow
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleSpans import (
    KNetTable,
    PoleRow,
)

KSectorUse = tuple[FacePlan, CornerUse, CapFrame]
KAxis = tuple[tuple[Fraction, ...], Fraction, int]


def SectorAxes(Frame: CapFrame, CornerInfo: CornerUse) -> tuple[KAxis, KAxis]:
    AxisU = (Frame.BaseU, CornerInfo.PointU, CornerInfo.SignU)
    AxisV = (Frame.BaseV, CornerInfo.PointV, CornerInfo.SignV)
    return (AxisU, AxisV) if CornerInfo.AlongI else (AxisV, AxisU)


def SectorRows(
    NetTable: KNetTable,
    SectorUse: KSectorUse,
    Context: tuple[int, Fraction],
) -> dict[KCapKey, KPoleRow]:
    PlanValue, CornerInfo, Frame = SectorUse
    Scale, Spacing = Context
    Found: dict[KCapKey, KPoleRow] = {}
    Reach = KReachSpans * Spacing
    IndicesU = AxisIndices(Frame.BaseU, CornerInfo.PointU, CornerInfo.SignU, Reach)
    IndicesV = AxisIndices(Frame.BaseV, CornerInfo.PointV, CornerInfo.SignV, Reach)
    for Column, IndexU in IndicesU.items():
        for RowIndex, IndexV in IndicesV.items():
            IndexI, IndexJ = (IndexU, IndexV) if CornerInfo.AlongI else (IndexV, IndexU)
            RowValue = PoleRow(
                NetTable,
                PlanValue.Cells,
                Scale,
                Frame.BaseU,
                Frame.BaseV,
                (RowIndex, Column),
            )
            if RowValue is not None:
                CapKey = SpokeKey(CornerInfo.Sector, CornerInfo.Valence, IndexI, IndexJ)
                _ = Found.setdefault(CapKey, RowValue)
    return Found


def IsUnitMix(Weights: KMapping[int, Fraction]) -> bool:
    return len(Weights) == 1 and next(iter(Weights.values())) == 1


def PlaceFrameMut(Frame: CapFrame, Found: dict[KCapKey, list[KPlaceKey]]) -> None:
    for CapKey in Frame.Keys.values():
        _ = Found.setdefault(CapKey, [])
    for RowIndex, Column in sorted(Frame.Places):
        RowMix, ColumnMix = Frame.MixV[RowIndex], Frame.MixU[Column]
        if not (IsUnitMix(RowMix) and IsUnitMix(ColumnMix)):
            continue
        BasePlace = (next(iter(RowMix)), next(iter(ColumnMix)))
        if BasePlace in Frame.Keys:
            Found[Frame.Keys[BasePlace]].append((Frame.Region, RowIndex, Column))


def CapPlacing(
    Frames: list[tuple[CapFrame, ...]],
) -> dict[int, dict[KCapKey, list[KPlaceKey]]]:
    Found: dict[int, dict[KCapKey, list[KPlaceKey]]] = {}
    for RegionFrames in Frames:
        for Frame in RegionFrames:
            PlaceFrameMut(Frame, Found.setdefault(Frame.Vertex, {}))
    return Found


def OneRequest(
    Graph: CageGraph,
    Vertex: int,
    SectorUses: dict[tuple[int, int], KSectorUse],
    Context: tuple[KNetTable, PoleMesh, int, int],
    Placing: dict[KCapKey, list[KPlaceKey]],
) -> CapInput:
    NetTable, MeshValue, Scale, Level = Context
    Valence = sum(1 for Entry in SectorUses if Entry[0] == Vertex)
    Sectors: list[CapSector] = []
    Reference: dict[KCapKey, KPoleRow] = {}
    for Sector in range(Valence):
        SectorUse = SectorUses[(Vertex, Sector)]
        AxisI, AxisJ = SectorAxes(SectorUse[2], SectorUse[1])
        Sectors.append(
            CapSector(SectorUse[1].FaceIndex, SectorKnots(*AxisI), SectorKnots(*AxisJ))
        )
        for CapKey, RowValue in SectorRows(
            NetTable, SectorUse, (Scale, CapSpacing(Scale, Level))
        ).items():
            _ = Reference.setdefault(CapKey, RowValue)
    return CapInput(
        Vertex,
        Valence,
        Level,
        tuple(Graph.Creased[LinkIndex] for LinkIndex in Graph.Fans[Vertex]),
        tuple(Sectors),
        LimitRow(MeshValue, Vertex, Level),
        Reference,
        {CapKey: tuple(Places) for CapKey, Places in Placing.items()},
        frozenset(Placing),
    )


def CapRequests(
    Graph: CageGraph,
    Plans: tuple[FacePlan, ...],
    Context: tuple[KNetTable, PoleMesh, int],
    Levels: KMapping[int, int],
    Frames: list[tuple[CapFrame, ...]],
) -> dict[int, CapInput]:
    NetTable, MeshValue, Scale = Context
    SectorUses = {
        (CornerInfo.Vertex, CornerInfo.Sector): (Plans[Frame.Region], CornerInfo, Frame)
        for RegionFrames in Frames
        for Frame in RegionFrames
        for CornerInfo in Frame.Uses
    }
    Placing = CapPlacing(Frames)
    return {
        Vertex: OneRequest(
            Graph,
            Vertex,
            SectorUses,
            (NetTable, MeshValue, Scale, Level),
            Placing.get(Vertex, {}),
        )
        for Vertex, Level in Levels.items()
    }
