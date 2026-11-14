from dataclasses import replace as ReplaceValue
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    SplineCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.JumpCurve import (
    OrderCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.OrderJumps import (
    CurveOrders,
    SurfaceOrders,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListTsplines import ListTsplines
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageResult import (
    CageResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import (
    ConvertCage,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.SwapFormCage import (
    SwapFormCage,
)
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface
from tests.convert.formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)
from tests.convert.formats.FusionCodec.Documents.Form.StencilArchives import (
    KStencilCages,
    KStencilStale,
)
from tests.convert.formats.FusionCodec.Documents.Form.StencilCases import (
    KStencilCases,
)
from tests.convert.formats.FusionCodec.Documents.Form.StencilNatives import (
    KStencilNatives,
)

KStencilSlack = 1e-12
KNeedZip = MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)


def FormLists(Model: DocumentModel) -> list[tuple[KJournalEntity, ...]]:
    Found = [
        BodyValue.History.Entities
        for BodyValue in Model.Bodies
        if isinstance(BodyValue.History, JournalModel)
        and ListTsplines(BodyValue.History.Entities)
    ]
    Found += [
        SnapValue.Snapshot.Entities
        for SnapValue in Model.Snapshots
        if isinstance(SnapValue.Snapshot, GeometryState)
        and ListTsplines(SnapValue.Snapshot.Entities)
    ]
    return Found


def PointGap(
    LeftPoints: tuple[tuple[float, ...], ...],
    RightPoints: tuple[tuple[float, ...], ...],
) -> float:
    assert len(LeftPoints) == len(RightPoints)
    return max(
        abs(LeftValue - RightValue)
        for LeftPoint, RightPoint in zip(LeftPoints, RightPoints)
        for LeftValue, RightValue in zip(LeftPoint, RightPoint, strict=True)
    )


def FaceCount(Entities: tuple[KJournalEntity, ...], Result: CageResult) -> int:
    Faces = {FaceValue.FaceIndex: FaceValue for FaceValue in Result.Faces}
    Found = ListTsplines(Entities)
    for Stored in Found:
        FaceValue = Faces[Stored.FaceIndex]
        Cache = Stored.Cache
        assert (Cache.KnotsU, Cache.KnotsV) == (
            FaceValue.Surface.KnotsU,
            FaceValue.Surface.KnotsV,
        )
        assert PointGap(Cache.Points, FaceValue.Surface.Points) <= KStencilSlack
        assert Stored.Jumps == FaceValue.Jumps == SurfaceOrders(Cache)
    return len(Found)


def EdgeCount(Entities: tuple[KJournalEntity, ...], Result: CageResult) -> int:
    Count = 0
    for Entity in Entities:
        if not isinstance(Entity, IntcurveNode):
            continue
        Curve = SplineCurve(Entity.Curve)
        Matches = [
            Index
            for Index, Other in enumerate(Result.Curves)
            if (Other.Knots, Other.Multiplicity) == (Curve.Knots, Curve.Multiplicity)
            and PointGap(Other.Poles, Curve.Poles) <= KStencilSlack
        ]
        assert len(Matches) == 1
        Lists = Result.CurveJumps[Matches[0]]
        assert Lists == CurveOrders(Curve)
        assert OrderCurve(Curve, Lists) == Entity.Curve
        Count += 1
    return Count


def PlaceCount(Entities: tuple[KJournalEntity, ...], Result: CageResult) -> int:
    Count = 0
    for Entity in Entities:
        if isinstance(Entity, PointNode):
            PointGaps = [
                PointGap((Other,), (Entity.PositionCm,)) for Other in Result.Points
            ]
            assert min(PointGaps) <= KStencilSlack
            Count += 1
    return Count


def StencilCounts(Model: DocumentModel, Result: CageResult) -> list[int]:
    Lists = FormLists(Model)
    assert Lists
    return [
        sum(FaceCount(Entities, Result) for Entities in Lists),
        sum(EdgeCount(Entities, Result) for Entities in Lists),
        sum(PlaceCount(Entities, Result) for Entities in Lists),
    ]


@KNeedZip
@MarkTests.parametrize(
    "CaseValue", KStencilNatives, ids=lambda CaseValue: FilePath(CaseValue[0]).stem
)
def TestNativeCage(CaseValue: tuple[str, str, str]) -> None:
    Model = ReadDocument(ReadFormFile(CaseValue[0], CaseValue[1]))
    Counts = StencilCounts(Model, ConvertCage(Model.Forms[0].Surface))
    assert min(Counts) > 0


@KNeedZip
@MarkTests.parametrize("CaseValue", KStencilCases, ids=lambda CaseValue: CaseValue[0])
def TestStencilSwap(CaseValue: tuple[str, str, str, str, str, str]) -> None:
    Model = ReadDocument(ReadFormFile(CaseValue[1], CaseValue[2]))
    Surface = ReadTspline(ReadFormFile(CaseValue[3], CaseValue[4]))
    Swapped = SwapFormCage(Model, Surface)
    Payload = EmitParsed(Swapped)
    assert HashBytes(Payload).hexdigest() == CaseValue[5]
    assert ReadDocument(Payload) == Swapped
    assert Swapped.Graphics is None
    assert Swapped.Forms[0].Surface == Surface
    assert min(StencilCounts(Swapped, ConvertCage(Surface))) > 0


@MarkTests.parametrize(
    "CaseValue", KStencilCages, ids=lambda CaseValue: FilePath(CaseValue[0]).stem
)
def TestStencilCage(CaseValue: tuple[str, str, int]) -> None:
    Surface = ReadTspline(ReadFormFile(CaseValue[0], CaseValue[1]))
    CheckSurface(Surface)
    Valence: dict[int, int] = {}
    for LinkValue in Surface.Topology.Links:
        Valence[LinkValue.VertexIndex] = Valence.get(LinkValue.VertexIndex, 0) + 1
    assert max(Valence.values()) == CaseValue[2]


@KNeedZip
def TestCageFault() -> None:
    Model = ReadDocument(ReadFormFile(*KStencilNatives[0][:2]))
    Surface = Model.Forms[0].Surface
    Heavy = ReplaceValue(Surface.Grips[0], Weight=1.5)
    Weighted = ReplaceValue(Surface, Grips=(Heavy, *Surface.Grips[1:]))
    assert any(FaceValue.Surface.Weights for FaceValue in ConvertCage(Weighted).Faces)
    Edges = tuple(
        ReplaceValue(EdgeValue, KnotInterval=2.0)
        for EdgeValue in Surface.Topology.Edges
    )
    Spread = ReplaceValue(Surface, Topology=ReplaceValue(Surface.Topology, Edges=Edges))
    Narrow, Widened = ConvertCage(Surface), ConvertCage(Spread)
    assert [FaceValue.Surface.KnotsU[-1].Value for FaceValue in Widened.Faces] == [
        2.0 * FaceValue.Surface.KnotsU[-1].Value for FaceValue in Narrow.Faces
    ]
    assert (
        max(
            abs(LeftValue - RightValue)
            for LeftPoint, RightPoint in zip(Widened.Points, Narrow.Points, strict=True)
            for LeftValue, RightValue in zip(LeftPoint, RightPoint, strict=True)
        )
        <= KStencilSlack
    )
    with RaisesError(ValueError, match="same cage layout"):
        _ = SwapFormCage(Model, Spread)
    Other = next(CaseValue for CaseValue in KStencilNatives if CaseValue[2] != "Box")
    Elsewhere = ReadDocument(ReadFormFile(*Other[:2])).Forms[0].Surface
    with RaisesError(ValueError, match="same cage layout"):
        _ = SwapFormCage(Model, Elsewhere)


@KNeedZip
def TestStaleCage() -> None:
    Model = ReadDocument(ReadFormFile(*KStencilStale))
    with RaisesError(ValueError, match="stale converted surface"):
        _ = SwapFormCage(Model, Model.Forms[0].Surface)
