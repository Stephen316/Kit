from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.ConvertGrid import (
    ConvertGrid,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import (
    ConvertForm,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
    FormFace,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.GridBody import (
    GridBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageBody import CageBody
from convert.formats.Fusion.DocumentCodec.Form.EmitFormDoc import EmitFormDoc
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.Model.KnotSurface import KnotSurface
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.convert.formats.FusionCodec.Documents.Form.ReadConverted import (
    ReadConverted,
)
from tests.convert.formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)
from tests.convert.formats.FusionCodec.Documents.Form.CageDocuments import (
    KCageDocuments,
)
from tests.convert.formats.FusionCodec.Documents.Form.StencilArchives import (
    KStencilUnknown,
)
from tests.convert.formats.FusionCodec.Documents.Form.StencilNatives import (
    KStencilNatives,
)

KCageSlack = 1e-12
KUniformSave = (
    "re/Fusion/LocalOracle/FormDocuments/Intervals/Box/Uniform2.f3d",
    "ea2495bf176e9845309a4af79ddffc3365e70b6ea7f6c67f445e2b74cf8da2eb",
)
KSingleSave = (
    "re/Fusion/LocalOracle/FormDocuments/Intervals/Box/Single.f3d",
    "07e17a88513b7ebe8ee3098ae439e5b2eb9abff022f71dc47fea86ed4c29e73d",
)
KNeedZip = MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)


def CageLayout(Surface: TsplineSurface) -> tuple[object, ...]:
    Header = Surface.Header
    return (
        Header.Degree,
        Header.CapType,
        Header.StarSmoothness,
        Header.UnitScale,
        Header.EndConditions,
        Header.StarKnotRule,
        Header.Tolerance,
        Header.GeometryTol,
        Surface.Topology,
        Surface.Mapping,
        Surface.Creases,
        Surface.SmartGrips,
        len(Surface.Grips),
    )


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


def TraceSpread(LeftCurve: BsCurve, RightCurve: BsCurve) -> float:
    assert ReplaceValue(LeftCurve, Poles=()) == ReplaceValue(RightCurve, Poles=())
    return PointSpread(LeftCurve.Poles, RightCurve.Poles)


def EdgeSpread(LeftEdge: FormEdge, RightEdge: FormEdge) -> float:
    Plain = ReplaceValue(LeftEdge, Curve=RightEdge.Curve, Label="", Windows=())
    assert Plain == ReplaceValue(RightEdge, Label="", Windows=())
    assert [Window.Face for Window in LeftEdge.Windows] == [
        Window.Face for Window in RightEdge.Windows
    ]
    Windows = PointSpread(
        tuple(
            (Entry.ULow, Entry.UHigh, Entry.VLow, Entry.VHigh)
            for Entry in LeftEdge.Windows
        ),
        tuple(
            (Entry.ULow, Entry.UHigh, Entry.VLow, Entry.VHigh)
            for Entry in RightEdge.Windows
        ),
    )
    return max(Windows, TraceSpread(LeftEdge.Curve, RightEdge.Curve))


def FaceSpread(LeftFace: FormFace, RightFace: FormFace) -> float:
    LeftCache, RightCache = LeftFace.Surface.Cache, RightFace.Surface.Cache
    assert ReplaceValue(LeftCache, Points=()) == ReplaceValue(RightCache, Points=())
    assert ReplaceValue(LeftFace.Surface, Cache=RightCache) == RightFace.Surface
    assert (LeftFace.DoubleSided, LeftFace.Contained) == (
        RightFace.DoubleSided,
        RightFace.Contained,
    )
    Spreads = [PointSpread(LeftCache.Points, RightCache.Points)]
    for LeftUse, RightUse in zip(LeftFace.Uses, RightFace.Uses, strict=True):
        assert (LeftUse.EdgeIndex, LeftUse.Reversed) == (
            RightUse.EdgeIndex,
            RightUse.Reversed,
        )
        Spreads.append(TraceSpread(LeftUse.Pcurve, RightUse.Pcurve))
        Spreads.append(abs(LeftUse.Fit - RightUse.Fit))
    return max(Spreads)


def ShapeSpread(Built: FormBody, Native: FormBody) -> float:
    assert Built.Regions == Native.Regions
    Spreads = [PointSpread(Built.PointsCm, Native.PointsCm)]
    Spreads += [
        EdgeSpread(LeftEdge, RightEdge)
        for LeftEdge, RightEdge in zip(Built.Edges, Native.Edges, strict=True)
    ]
    Spreads += [
        FaceSpread(LeftFace, RightFace)
        for LeftFace, RightFace in zip(Built.Faces, Native.Faces, strict=True)
    ]
    return max(Spreads)


@KNeedZip
@MarkTests.parametrize(
    "CaseValue", KStencilNatives, ids=lambda CaseValue: FilePath(CaseValue[0]).stem
)
def TestCageBody(CaseValue: tuple[str, str, str]) -> None:
    Model = ReadDocument(ReadFormFile(CaseValue[0], CaseValue[1]))
    Surface = Model.Forms[0].Surface
    Built = CageBody(Surface)
    assert ShapeSpread(Built, ReadConverted(Model)) <= KCageSlack
    assert ConvertForm(Surface) == Built


@KNeedZip
@MarkTests.parametrize("CaseValue", KCageDocuments, ids=lambda CaseValue: CaseValue[0])
def TestCageDoc(CaseValue: tuple[str, str, str, str, str, str, str]) -> None:
    Surface = ReadTspline(ReadFormFile(CaseValue[1], CaseValue[2]))
    Built = ConvertForm(Surface)
    Stored = ReadDocument(ReadFormFile(CaseValue[3], CaseValue[4]))
    assert Stored.Forms[0].Surface == Surface
    assert ShapeSpread(Built, ReadConverted(Stored)) <= KCageSlack
    Oracle = ReadDocument(ReadFormFile(CaseValue[5], CaseValue[6]))
    assert Oracle.Forms[0].Surface.Grips == Surface.Grips
    assert CageLayout(Oracle.Forms[0].Surface) == CageLayout(Surface)
    assert ShapeSpread(Built, ReadConverted(Oracle)) <= KCageSlack
    Emitted = ReadDocument(EmitFormDoc(FormSpec("Kit Form", Surface, Built)))
    assert Emitted.Forms[0].Surface == Surface
    assert ReadConverted(Emitted) == Built


@KNeedZip
def TestFormChoice() -> None:
    Plane = ReadDocument(ReadFormFile(*KStencilUnknown)).Forms[0].Surface
    assert ConvertForm(Plane) == GridBody(ConvertGrid(Plane))
    Creased = next(
        CaseValue for CaseValue in KStencilNatives if CaseValue[2] == "CreasedPlane"
    )
    Folded = ReadDocument(ReadFormFile(*Creased[:2])).Forms[0].Surface
    assert ConvertForm(Folded) == CageBody(Folded)
    Model = ReadDocument(ReadFormFile(*KStencilNatives[0][:2]))
    Surface = Model.Forms[0].Surface
    Heavy = ReplaceValue(Surface.Grips[0], Weight=1.5)
    Weighted = ReplaceValue(Surface, Grips=(Heavy, *Surface.Grips[1:]))
    Rational = ConvertForm(Weighted)
    assert Rational == CageBody(Weighted)
    assert any(FaceValue.Surface.Cache.Weights for FaceValue in Rational.Faces)


@KNeedZip
def TestUniformSpan() -> None:
    Model = ReadDocument(ReadFormFile(*KUniformSave))
    Surface = Model.Forms[0].Surface
    assert {EdgeValue.KnotInterval for EdgeValue in Surface.Topology.Edges} == {2.0}
    assert ShapeSpread(ConvertForm(Surface), ReadConverted(Model)) <= KCageSlack


@KNeedZip
def TestEdgeKnots() -> None:
    Surface = ReadDocument(ReadFormFile(*KSingleSave)).Forms[0].Surface
    assert isinstance(Surface, KnotSurface)
    Intervals = tuple(EdgeValue.KnotInterval for EdgeValue in Surface.Topology.Edges)
    assert Surface.EdgeKnots == Intervals
    assert len(set(Intervals)) > 1
    Shifted = ReplaceValue(Surface, EdgeKnots=(2.0, *Surface.EdgeKnots[1:]))
    with RaisesError(ValueError, match="edge knot records"):
        _ = ConvertForm(Shifted)
