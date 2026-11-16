from dataclasses import replace as ReplaceValue
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as MarkTests, raises as RaisesError

from convert.Formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    SplineCurve,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Conversion.ConvertGrid import (
    ConvertGrid,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridResult import (
    GridResult,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Conversion.JumpCurve import (
    JumpCurve,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.Formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Form.SwapGridCage import (
    SwapGridCage,
)
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.Formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.Convert.Formats.FusionCodec.Documents.Form.GridArchives import (
    KGridArchives,
    KGridCages,
    KGridRefusals,
    KShiftedCache,
)
from tests.Convert.Formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)

# the pole slack cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KPoleSlack = 1e-15

# the plane carrier cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KPlaneCarrier = KGridArchives[4]

# the other layout cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KOtherLayout = next(
    CaseValue for CaseValue in KGridArchives if CaseValue[0].endswith("Plane3x2.f3d")
)

# the need zip cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KNeedZip = MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)


# shared form entities setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def FormEntities(Model: DocumentModel) -> list[tuple[KJournalEntity, ...]]:
    Found = [
        BodyValue.History.Entities
        for BodyValue in Model.Bodies
        if isinstance(BodyValue.History, JournalModel)
    ]
    Found += [
        SnapValue.Snapshot.Entities
        for SnapValue in Model.Snapshots
        if isinstance(SnapValue.Snapshot, GeometryState)
    ]
    return Found


# shared point gap setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
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


# shared grid counts setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def GridCounts(Model: DocumentModel, Result: GridResult, Slack: float) -> list[int]:
    Counts = [0, 0, 0]
    for Entities in FormEntities(Model):
        for Entity in Entities:
            if isinstance(Entity, SplineNode) and isinstance(
                Entity.Surface, TsplineSurf
            ):
                Cache = Entity.Surface.Cache
                assert (Cache.KnotsU, Cache.KnotsV) == (
                    Result.Surface.KnotsU,
                    Result.Surface.KnotsV,
                )
                assert PointGap(Cache.Points, Result.Surface.Points) <= Slack
                Subtrans = Entity.Surface.Subtrans
                if isinstance(Subtrans, SubtransNode):
                    assert Subtrans.Regions == (Result.Patches,)
                assert Entity.Surface.Jumps == Result.SurfaceJumps
                Counts[0] += 1
            elif isinstance(Entity, IntcurveNode):
                Curve = SplineCurve(Entity.Curve)
                Matches = [
                    Index
                    for Index, Bound in enumerate(Result.Bounds)
                    if (Bound.Knots, Bound.Multiplicity)
                    == (Curve.Knots, Curve.Multiplicity)
                    and PointGap(Bound.Poles, Curve.Poles) <= Slack
                ]
                assert len(Matches) == 1
                assert JumpCurve(Curve, Result.BoundJumps[Matches[0]]) == Entity.Curve
                Counts[1] += 1
            elif isinstance(Entity, PointNode):
                CornerGaps = [
                    PointGap((Corner,), (Entity.PositionCm,))
                    for Corner in Result.Corners
                ]
                assert min(CornerGaps) <= Slack
                Counts[2] += 1
    return Counts


# the grid native contract needs boundary coverage so stored document relationships remain consistent
@KNeedZip
@MarkTests.parametrize(
    "CaseValue", KGridArchives, ids=lambda CaseValue: FilePath(CaseValue[0]).stem
)
def TestGridNative(CaseValue: tuple[str, str]) -> None:
    Model = ReadDocument(ReadFormFile(*CaseValue))
    Result = ConvertGrid(Model.Forms[0].Surface)
    assert GridCounts(Model, Result, KPoleSlack) == [2, 8, 8]


# the grid refuse contract needs boundary coverage so stored document relationships remain consistent
@KNeedZip
@MarkTests.parametrize(
    "CaseValue", KGridRefusals, ids=lambda CaseValue: FilePath(CaseValue[0]).stem
)
def TestGridRefuse(CaseValue: tuple[str, str, str]) -> None:
    Model = ReadDocument(ReadFormFile(CaseValue[0], CaseValue[1]))
    with RaisesError(ValueError, match=CaseValue[2]):
        _ = ConvertGrid(Model.Forms[0].Surface)


# the grid swap contract needs boundary coverage so stored document relationships remain consistent
@KNeedZip
@MarkTests.parametrize(
    "CaseValue", KGridCages, ids=lambda CaseValue: FilePath(CaseValue[0]).stem
)
def TestGridSwap(CaseValue: tuple[str, str, str]) -> None:
    Model = ReadDocument(ReadFormFile(*KPlaneCarrier))
    Surface = ReadTspline(ReadFormFile(CaseValue[0], CaseValue[1]))
    Swapped = SwapGridCage(Model, Surface)
    Payload = EmitParsed(Swapped)
    assert HashBytes(Payload).hexdigest() == CaseValue[2]
    assert ReadDocument(Payload) == Swapped
    assert Swapped.Graphics is None
    assert Swapped.Forms[0].Surface == Surface
    assert GridCounts(Swapped, ConvertGrid(Surface), 0.0) == [2, 8, 8]


# shared break cage setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def BreakCage(Surface: TsplineSurface, Fault: str) -> TsplineSurface:
    if Fault == "weight":
        Grips = (ReplaceValue(Surface.Grips[0], Weight=1.5), *Surface.Grips[1:])
        return ReplaceValue(Surface, Grips=Grips)
    if Fault == "mapping":
        return ReplaceValue(Surface, Mapping=None)
    Vertices = Surface.Topology.Vertices
    Turned = (ReplaceValue(Vertices[0], Direction="NORTH"), *Vertices[1:])
    Topology = ReplaceValue(Surface.Topology, Vertices=Turned)
    return ReplaceValue(Surface, Topology=Topology)


# the grid fault contract needs boundary coverage so stored document relationships remain consistent
@KNeedZip
@MarkTests.parametrize("Fault", ("weight", "mapping", "direction"))
def TestGridFault(Fault: str) -> None:
    Model = ReadDocument(ReadFormFile(*KPlaneCarrier))
    with RaisesError(ValueError):
        _ = ConvertGrid(BreakCage(Model.Forms[0].Surface, Fault))
    with RaisesError(ValueError):
        _ = SwapGridCage(Model, BreakCage(Model.Forms[0].Surface, Fault))


# the grid stale contract needs boundary coverage so stored document relationships remain consistent
@KNeedZip
def TestGridStale() -> None:
    Model = ReadDocument(ReadFormFile(*KShiftedCache))
    with RaisesError(ValueError, match="stale converted surface"):
        _ = SwapGridCage(Model, Model.Forms[0].Surface)


# the grid layout contract needs boundary coverage so stored document relationships remain consistent
@KNeedZip
def TestGridLayout() -> None:
    Model = ReadDocument(ReadFormFile(*KPlaneCarrier))
    Other = ReadDocument(ReadFormFile(*KOtherLayout)).Forms[0].Surface
    with RaisesError(ValueError, match="same grid layout"):
        _ = SwapGridCage(Model, Other)
