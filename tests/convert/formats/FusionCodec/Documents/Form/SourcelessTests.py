from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from typing import cast as CastValue

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.ConvertGrid import (
    ConvertGrid,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.CreateFormBrep import (
    CreateFormBrep,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormWindow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormMarks import (
    FormMarks,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.GridBody import (
    GridBody,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.DocumentCodec.Form.EmitFormDoc import EmitFormDoc
from convert.formats.Fusion.DocumentCodec.Form.FormLabels import FormLabels
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.convert.formats.FusionCodec.Documents.Form.GridArchives import KGridCages
from tests.convert.formats.FusionCodec.Documents.Form.ReadConverted import (
    ActiveNodes,
    BodyType,
    CachedEntity,
    ClearTags,
    HistoryMicros,
    KTagWindows,
    ReadConverted,
    TagWindows,
)
from tests.convert.formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)

KPoleSlack = 1e-15
KLabelSet = {"1", "2", "3", "4", "5"}
KNeedZip = MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)
KPlanePrimitives: tuple[tuple[str, str], ...] = (
    (
        "re/Fusion/LocalOracle/FormDocuments/Grid/Primitives/Plane1x1.f3d",
        "7485f0f76c1b1802fd3d539ac7d826c38d13ee407ca2616ad066ea748e8fd908",
    ),
    (
        "re/Fusion/LocalOracle/FormDocuments/Grid/Primitives/Plane2x5.f3d",
        "0d0d28c44c9cb2919f7642a8eb3402c95adcf86bdea2e3d7ea45803091c9a6bc",
    ),
    (
        "re/Fusion/LocalOracle/FormDocuments/Grid/Primitives/Plane3x2.f3d",
        "59c1f79b6bbe739774fbbb2b1eea2f5ef9719588171951941ae4b6a21bed6ba3",
    ),
    (
        "re/Fusion/LocalOracle/FormDocuments/Grid/Primitives/Plane4x4.f3d",
        "a19a4d0601ada4760877c39ae3976dd681ba5b7ed9b9b53b005ca16c349dcc42",
    ),
    (
        "re/Fusion/LocalOracle/TSpline/Plane.f3d",
        "a81662369ddd6407b98975c335d6510b2eb9c7445214617e1df2e248c0d19612",
    ),
)
KClosedControls: tuple[tuple[str, str], ...] = (
    (
        "re/Fusion/LocalOracle/TSpline/Box.f3d",
        "24f533c68c2efb8e718789b79a4c3494d504f8f224a040b527db806e9b4d7a45",
    ),
    (
        "re/Fusion/LocalOracle/TSpline/SymmetricBox.f3d",
        "d6af6d6a493d7ca8436c660bf1ba4be32d9d5d9f5c873f8582ba4002a43e4d21",
    ),
    (
        "re/Fusion/LocalOracle/TSplineCodec/vendor_BoxCreasedControl.f3d",
        "6f644a8c2af88f6e21baca6e8c62b7e381bcadba4cf87957e87648873445e815",
    ),
    (
        "re/Fusion/LocalOracle/TSplineCodec/vendor_PlaneCreasedControl.f3d",
        "b2a7661e07216078072f69c17c13c5e09c0995cf2e582208a4bffb77b09d9031",
    ),
)
KNativeBodies = KPlanePrimitives + KClosedControls
KEmitCases = (KPlanePrimitives[2], KPlanePrimitives[4], *KClosedControls)
KRefusals: tuple[tuple[str, str], ...] = (
    ("label", "face label must be a positive integer"),
    ("range", "pcurve range differs from its edge curve"),
    ("window", "edge window names no cage face"),
    ("unique", "labels must be unique"),
    ("closed", "closed edges need a closed curve"),
    ("spec", "typed Fusion Form document specification"),
    ("text", "Invalid Form document text"),
)


def CaseName(CaseValue: tuple[str, ...]) -> str:
    return FilePath(CaseValue[0]).stem


def PointSpread(
    LeftPoints: tuple[tuple[float, ...], ...],
    RightPoints: tuple[tuple[float, ...], ...],
) -> float:
    assert len(LeftPoints) == len(RightPoints)
    return max(
        (
            abs(LeftValue - RightValue)
            for LeftPoint, RightPoint in zip(LeftPoints, RightPoints)
            for LeftValue, RightValue in zip(LeftPoint, RightPoint, strict=True)
        ),
        default=0.0,
    )


def CurveSpread(LeftCurve: BsCurve, RightCurve: BsCurve) -> float:
    assert ReplaceValue(LeftCurve, Poles=()) == ReplaceValue(RightCurve, Poles=())
    return PointSpread(LeftCurve.Poles, RightCurve.Poles)


def WindowSpread(
    LeftWindows: tuple[FormWindow, ...], RightWindows: tuple[FormWindow, ...]
) -> float:
    assert [Window.Face for Window in LeftWindows] == [
        Window.Face for Window in RightWindows
    ]
    return PointSpread(
        tuple(
            (Window.ULow, Window.UHigh, Window.VLow, Window.VHigh)
            for Window in LeftWindows
        ),
        tuple(
            (Window.ULow, Window.UHigh, Window.VLow, Window.VHigh)
            for Window in RightWindows
        ),
    )


def BodySpread(Built: FormBody, Native: FormBody) -> float:
    assert Built.Regions == Native.Regions
    Spreads = [PointSpread(Built.PointsCm, Native.PointsCm)]
    for LeftEdge, RightEdge in zip(Built.Edges, Native.Edges, strict=True):
        assert ReplaceValue(LeftEdge, Curve=RightEdge.Curve, Label="", Windows=()) == (
            ReplaceValue(RightEdge, Label="", Windows=())
        )
        Spreads.append(CurveSpread(LeftEdge.Curve, RightEdge.Curve))
        Spreads.append(WindowSpread(LeftEdge.Windows, RightEdge.Windows))
    for LeftFace, RightFace in zip(Built.Faces, Native.Faces, strict=True):
        LeftCache, RightCache = LeftFace.Surface.Cache, RightFace.Surface.Cache
        assert ReplaceValue(LeftCache, Points=()) == ReplaceValue(RightCache, Points=())
        assert (LeftFace.Surface.Jumps, LeftFace.Surface.Region) == (
            RightFace.Surface.Jumps,
            RightFace.Surface.Region,
        )
        assert (LeftFace.DoubleSided, LeftFace.Contained) == (
            RightFace.DoubleSided,
            RightFace.Contained,
        )
        Spreads.append(PointSpread(LeftCache.Points, RightCache.Points))
        for LeftUse, RightUse in zip(LeftFace.Uses, RightFace.Uses, strict=True):
            assert (LeftUse.EdgeIndex, LeftUse.Reversed) == (
                RightUse.EdgeIndex,
                RightUse.Reversed,
            )
            Spreads.append(CurveSpread(LeftUse.Pcurve, RightUse.Pcurve))
    return max(Spreads)


def IsClosedBody(Model: FormBody) -> bool:
    UseCount = sum(len(FaceValue.Uses) for FaceValue in Model.Faces)
    return UseCount == 2 * len(Model.Edges)


def AssertSolidity(Document: DocumentModel, Model: FormBody) -> None:
    assert BodyType(Document) == (2 if IsClosedBody(Model) else 4)
    Entity, NextId, Order = CachedEntity(Document)
    assert Order == (Entity,) and NextId == Entity + 1


def BodyLabels(Model: FormBody) -> set[str]:
    Labels = {FaceValue.Label for FaceValue in Model.Faces}
    return Labels | {EdgeValue.Label for EdgeValue in Model.Edges}


def DerivedWindows(Model: FormBody) -> KTagWindows:
    return {
        LabelValue.Label: (LabelValue.EntityType, LabelValue.Windows)
        for LabelValue in FormLabels(Model)
    }


def SnapEntities(Model: DocumentModel) -> tuple[object, ...]:
    assert len(Model.Snapshots) == 1
    Snapshot = Model.Snapshots[0].Snapshot
    assert isinstance(Snapshot, GeometryState)
    return Snapshot.Entities


def ReadMarks(Model: DocumentModel) -> FormMarks:
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    return FormMarks(History.Stamp, HistoryMicros(Model))


def EmitRead(Surface: TsplineSurface, Model: FormBody) -> DocumentModel:
    SpecValue = FormSpec("Kit Form", Surface, Model, "Body1", "Form1")
    Emitted = ReadDocument(EmitFormDoc(SpecValue))
    assert len(Emitted.Forms) == 1 and Emitted.Forms[0].Surface == Surface
    assert len(Emitted.Bodies) == 1
    assert ReadConverted(Emitted) == Model
    Rebuilt = CreateFormBrep(Surface, Model, ReadMarks(Emitted))
    assert Rebuilt.History.Entities == ActiveNodes(Emitted)
    assert Rebuilt.Snapshot.Entities == SnapEntities(Emitted)
    assert TagWindows(Emitted) == DerivedWindows(Model)
    AssertSolidity(Emitted, Model)
    return Emitted


def BreakEdge(Model: FormBody, Fault: str) -> FormBody:
    EdgeValue = Model.Edges[0]
    if Fault == "window":
        Outside = (FormWindow(1 << 20, 0.0, 1.0, 0.0, 0.0),)
        EdgeValue = ReplaceValue(EdgeValue, Windows=Outside)
    elif Fault == "unique":
        EdgeValue = ReplaceValue(EdgeValue, Label=Model.Faces[0].Label)
    else:
        EdgeValue = ReplaceValue(EdgeValue, EndVertex=EdgeValue.StartVertex)
    return ReplaceValue(Model, Edges=(EdgeValue, *Model.Edges[1:]))


def BreakFace(Model: FormBody, Fault: str) -> FormBody:
    FaceValue = Model.Faces[0]
    if Fault == "label":
        FaceValue = ReplaceValue(FaceValue, Label="x1")
    else:
        UseValue = FaceValue.Uses[0]
        Pcurve = ReplaceValue(UseValue.Pcurve, Knots=(0.0, 1.0e6))
        SideUses = (ReplaceValue(UseValue, Pcurve=Pcurve), *FaceValue.Uses[1:])
        FaceValue = ReplaceValue(FaceValue, Uses=SideUses)
    return ReplaceValue(Model, Faces=(FaceValue, *Model.Faces[1:]))


def BreakSpec(SpecValue: FormSpec, Fault: str) -> FormSpec:
    if Fault == "spec":
        Untyped = (SpecValue.Title, SpecValue.Surface, SpecValue.Body)
        return CastValue(FormSpec, Untyped)
    if Fault == "text":
        return ReplaceValue(SpecValue, Title="Form\x00")
    if Fault in ("label", "range"):
        return ReplaceValue(SpecValue, Body=BreakFace(SpecValue.Body, Fault))
    return ReplaceValue(SpecValue, Body=BreakEdge(SpecValue.Body, Fault))


@KNeedZip
@MarkTests.parametrize("CaseValue", KNativeBodies, ids=CaseName)
def TestRebuildBrep(CaseValue: tuple[str, str]) -> None:
    Model = ReadDocument(ReadFormFile(*CaseValue))
    Native = ReadConverted(Model)
    Surface = Model.Forms[0].Surface
    Rebuilt = CreateFormBrep(Surface, Native, ReadMarks(Model))
    assert ClearTags(Rebuilt.History.Entities) == ClearTags(ActiveNodes(Model))
    assert Rebuilt.Snapshot.Entities == SnapEntities(Model)
    assert DerivedWindows(Native) == TagWindows(Model)
    AssertSolidity(Model, Native)


@KNeedZip
@MarkTests.parametrize("CaseValue", KPlanePrimitives, ids=CaseName)
def TestGridBody(CaseValue: tuple[str, str]) -> None:
    Model = ReadDocument(ReadFormFile(*CaseValue))
    Native = ReadConverted(Model)
    Built = GridBody(ConvertGrid(Model.Forms[0].Surface))
    assert BodySpread(Built, Native) <= KPoleSlack
    assert BodyLabels(Built) == BodyLabels(Native) == KLabelSet
    assert [FaceValue.Label for FaceValue in Built.Faces] == ["1"]
    assert [EdgeValue.Label for EdgeValue in Built.Edges] == ["2", "3", "4", "5"]


@KNeedZip
@MarkTests.parametrize("CaseValue", KEmitCases, ids=CaseName)
def TestEmitNative(CaseValue: tuple[str, str]) -> None:
    Model = ReadDocument(ReadFormFile(*CaseValue))
    Native = ReadConverted(Model)
    Emitted = EmitRead(Model.Forms[0].Surface, Native)
    assert TagWindows(Emitted) == TagWindows(Model)
    assert SnapEntities(Emitted) == SnapEntities(Model)


@KNeedZip
@MarkTests.parametrize("CaseValue", KGridCages, ids=CaseName)
def TestEmitGrid(CaseValue: tuple[str, str, str]) -> None:
    Surface = ReadTspline(ReadFormFile(CaseValue[0], CaseValue[1]))
    Built = GridBody(ConvertGrid(Surface))
    Emitted = EmitRead(Surface, Built)
    assert BodyLabels(ReadConverted(Emitted)) == KLabelSet


@MarkTests.parametrize(
    "Fault,Message", KRefusals, ids=[Refusal[0] for Refusal in KRefusals]
)
def TestFormRefuse(Fault: str, Message: str) -> None:
    Surface = ReadTspline(ReadFormFile(KGridCages[0][0], KGridCages[0][1]))
    SpecValue = FormSpec("Kit Form", Surface, GridBody(ConvertGrid(Surface)))
    with RaisesError(ValueError, match=Message):
        _ = EmitFormDoc(BreakSpec(SpecValue, Fault))
