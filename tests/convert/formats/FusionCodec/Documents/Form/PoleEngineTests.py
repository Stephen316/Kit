from dataclasses import replace as ReplaceValue
from fractions import Fraction
from typing import Mapping as KMapping

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
    ReadGraph,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedLayout import (
    CappedLayout,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.SolveCaps import SolveCaps
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import (
    KCapKey,
    CapInput,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleKnots import (
    CapPoints,
    FixedKnots,
    FixedPoints,
    IsCapPoint,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import KPoleRow
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleTable import BuildTable
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import (
    ApplyStencil,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilTable import (
    StencilTable,
)
from convert.formats.Fusion.TSplineCodec.Model.CreaseData import CreaseData
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from tests.convert.formats.FusionCodec.Documents.Form.CappedCages import (
    KCageParts,
    KCoords,
    BoxCreases,
    BoxParts,
    MakeSurface,
    PrismParts,
    TorusParts,
)

KRowSlack = 1e-12
KRoofCounts = (2, 3, 1)
KRidgeEnds = ((1.0, 0.0, 1.0), (1.0, 3.0, 1.0))
KTurnPath = ((0.0, 1.0, 2.0), (1.0, 1.0, 2.0), (1.0, 2.0, 2.0))
KLinePath = ((0.0, 1.0, 2.0), (1.0, 1.0, 2.0), (2.0, 1.0, 2.0))
KCubeKnots = (
    SplineKnot(0.0, 3),
    SplineKnot(0.125, 2),
    SplineKnot(0.25, 2),
    SplineKnot(0.5, 1),
    SplineKnot(0.75, 2),
    SplineKnot(0.875, 2),
    SplineKnot(1.0, 3),
)


class CallLog:
    def __init__(self) -> None:
        super().__init__()
        self.Requests: list[CapInput] = []

    def __call__(self, Request: CapInput) -> KMapping[KCapKey, KPoleRow]:
        self.Requests.append(Request)
        return SolveCaps(Request)


def SharpSurface() -> TsplineSurface:
    Parts = BoxParts((2, 2, 2))
    Plain = MakeSurface(Parts)
    return ReplaceValue(Plain, Creases=BoxCreases(Parts, Plain, 2.0))


def HasUnitRows(Table: StencilTable) -> bool:
    return all(
        abs(sum(Value for _, Value in RowValue) - 1.0) < KRowSlack
        for RowValue in Table.Rows
    )


def TestCubeKnots() -> None:
    Table = BuildTable(MakeSurface(BoxParts((1, 1, 1))))
    assert len(Table.Faces) == 6
    for FaceValue in Table.Faces:
        assert FaceValue.KnotsU == KCubeKnots
        assert FaceValue.KnotsV == KCubeKnots
        assert len(FaceValue.Poles) == 13 * 13


def TestCubeHook() -> None:
    Logger = CallLog()
    Table = BuildTable(MakeSurface(BoxParts((1, 1, 1))), Logger)
    assert len(Logger.Requests) == 8
    assert all(
        Request.Valence == 3 and Request.Level == 2 for Request in Logger.Requests
    )
    for Request in Logger.Requests:
        assert ("ep",) in Request.Unknown
        assert len(Request.Sectors) == 3
        assert Request.Limit is not None
        assert all(
            CapKey in Request.Reference for CapKey in (("spoke", 0, 2), ("in", 0, 2, 2))
        )
        assert len(Request.Places[("ep",)]) == 3
    assert HasUnitRows(Table)


def TestRowSums() -> None:
    for Parts in (BoxParts((2, 3, 4)), PrismParts(5), PrismParts(6)):
        assert HasUnitRows(BuildTable(MakeSurface(Parts)))


def TestSharpBox() -> None:
    Logger = CallLog()
    Table = BuildTable(SharpSurface(), Logger)
    assert Logger.Requests == []
    Plain = (SplineKnot(0.0, 3), SplineKnot(1.0, 1), SplineKnot(2.0, 3))
    assert all(
        FaceValue.KnotsU == Plain and FaceValue.KnotsV == Plain
        for FaceValue in Table.Faces
    )
    assert (len(Table.Faces), len(Table.Curves), len(Table.Points)) == (6, 12, 8)
    assert HasUnitRows(Table)


def TestTorusFace() -> None:
    Logger = CallLog()
    Table = BuildTable(MakeSurface(TorusParts((8, 6))), Logger)
    assert Logger.Requests == []
    assert len(Table.Faces) == 1
    FaceValue = Table.Faces[0]
    assert (FaceValue.KnotsU[0].Count, FaceValue.KnotsU[-1].Count) == (3, 3)
    assert len(FaceValue.Poles) == (8 + 3) * (6 + 3)
    assert HasUnitRows(Table)


def TestCurveEnds() -> None:
    Table = BuildTable(MakeSurface(BoxParts((2, 3, 4))))
    PointRows = {Table.Rows[Index] for Index in Table.Points}
    for CurveValue in Table.Curves:
        assert CurveValue.Multiplicity[0] == CurveValue.Multiplicity[-1] == 3
        assert len(CurveValue.Poles) == sum(CurveValue.Multiplicity) - 2
        assert Table.Rows[CurveValue.Poles[0]] in PointRows
        assert Table.Rows[CurveValue.Poles[-1]] in PointRows


def IsBoxEdge(First: KCoords, Second: KCoords) -> bool:
    Bounds = [
        AxisIndex
        for AxisIndex in range(3)
        if First[AxisIndex] == Second[AxisIndex]
        and First[AxisIndex] in (0.0, float(KRoofCounts[AxisIndex]))
    ]
    return len(Bounds) >= 2


def IsRidgeEdge(First: KCoords, Second: KCoords) -> bool:
    return all(
        Point[0] == 1.0 and Point[2] == float(KRoofCounts[2])
        for Point in (First, Second)
    )


def RoofSurface(IsListed: bool) -> TsplineSurface:
    Parts = BoxParts(KRoofCounts)
    Plain = MakeSurface(Parts)
    Links = Plain.Topology.Links
    Creased = [
        LinkValue
        for LinkValue in Links
        if IsBoxEdge(
            Parts[0][LinkValue.VertexIndex],
            Parts[0][Links[LinkValue.NextLink].VertexIndex],
        )
        or IsRidgeEdge(
            Parts[0][LinkValue.VertexIndex],
            Parts[0][Links[LinkValue.NextLink].VertexIndex],
        )
    ]
    Edges = tuple(sorted({LinkValue.EdgeIndex for LinkValue in Creased}))
    Listed = sorted({LinkValue.VertexIndex for LinkValue in Creased})
    return ReplaceValue(
        Plain, Creases=CreaseData(Edges, tuple(Listed) if IsListed else ())
    )


def PathGraph(Parts: KCageParts, PathPoints: tuple[KCoords, ...]) -> CageGraph:
    Plain = MakeSurface(Parts)
    Links = Plain.Topology.Links
    Steps = {frozenset(StepPair) for StepPair in zip(PathPoints, PathPoints[1:])}
    Edges = {
        LinkValue.EdgeIndex
        for LinkValue in Links
        if frozenset(
            (
                Parts[0][LinkValue.VertexIndex],
                Parts[0][Links[LinkValue.NextLink].VertexIndex],
            )
        )
        in Steps
    }
    return ReadGraph(ReplaceValue(Plain, Creases=CreaseData(tuple(sorted(Edges)), ())))


def TestRoofFixed() -> None:
    Parts = BoxParts(KRoofCounts)
    Graph = ReadGraph(RoofSurface(False))
    EndLevels = {Parts[0].index(Point): 2 for Point in KRidgeEnds}
    assert FixedPoints(Graph) == EndLevels
    assert CapPoints(Graph) == {}
    Halves = (Fraction(1, 2), Fraction(1, 4), Fraction(1, 8))
    assert FixedKnots(2) == tuple((Value, 1) for Value in Halves)


def TestRoofTable() -> None:
    Logger = CallLog()
    Table = BuildTable(RoofSurface(False), Logger)
    assert Logger.Requests == []
    assert len(Table.Faces) == 9
    assert HasUnitRows(Table)


def TestListedRoof() -> None:
    Plain = BuildTable(RoofSurface(False))
    Listed = BuildTable(RoofSurface(True))
    assert Listed.Faces == Plain.Faces
    assert Listed.Rows == Plain.Rows


def TestTurnCaps() -> None:
    Parts = BoxParts((2, 2, 2))
    Middle = Parts[0].index(KTurnPath[1])
    Start = Parts[0].index(KTurnPath[0])
    assert IsCapPoint(PathGraph(Parts, KTurnPath), Middle)
    LineGraph = PathGraph(Parts, KLinePath)
    assert not IsCapPoint(LineGraph, Middle)
    assert IsCapPoint(LineGraph, Start)
    assert FixedPoints(LineGraph) == {}


def TestApplyTable() -> None:
    Surface = MakeSurface(BoxParts((1, 1, 1)))
    Heavy = ReplaceValue(Surface.Grips[0], Weight=2.0)
    Weighted = ReplaceValue(Surface, Grips=(Heavy,) + Surface.Grips[1:])
    Result = ApplyStencil(BuildTable(Weighted), Weighted, CappedLayout(Weighted))
    assert len(Result.Faces) == 6
    assert len(Result.Points) == 8
