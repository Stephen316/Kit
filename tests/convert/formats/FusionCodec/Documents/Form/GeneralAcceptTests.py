from dataclasses import replace as ReplaceValue
from sys import version_info as PythonVersion

from pytest import approx as ApproxValue, mark as MarkTests

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import (
    ConvertForm,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
    FormFace,
    FormWindow,
)
from convert.formats.Fusion.DocumentCodec.Form.EmitFormDoc import EmitFormDoc
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.convert.formats.FusionCodec.Documents.Form.CapCases import KCapCases
from tests.convert.formats.FusionCodec.Documents.Form.CappedCages import (
    BoxCreases,
    BoxParts,
    MakeSurface,
)
from tests.convert.formats.FusionCodec.Documents.Form.GeneralCases import (
    KGeneralCases,
)
from tests.convert.formats.FusionCodec.Documents.Form.GridArchives import KPlanarArea
from tests.convert.formats.FusionCodec.Documents.Form.ReadConverted import (
    ReadConverted,
)
from tests.convert.formats.FusionCodec.Documents.Materials.MaterialFields import (
    MaterialFields,
)
from tests.convert.formats.FusionCodec.Documents.NamedGroups import NamedGroups
from tests.convert.formats.FusionCodec.Documents.Rectangle.RectValues import (
    ReadPoint,
    ReadScalar,
)
from tests.convert.formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)

KGeneralSlack = 1e-12
KNeedZip = MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)


def ValueSpread(LeftValues: tuple[float, ...], RightValues: tuple[float, ...]) -> float:
    assert len(LeftValues) == len(RightValues)
    return max(
        (
            abs(LeftValue - RightValue)
            for LeftValue, RightValue in zip(LeftValues, RightValues)
        ),
        default=0.0,
    )


def PointSpread(
    LeftPoints: tuple[tuple[float, ...], ...],
    RightPoints: tuple[tuple[float, ...], ...],
) -> float:
    assert len(LeftPoints) == len(RightPoints)
    return max(
        (
            ValueSpread(LeftPoint, RightPoint)
            for LeftPoint, RightPoint in zip(LeftPoints, RightPoints)
        ),
        default=0.0,
    )


def CurveSpread(LeftCurve: BsCurve, RightCurve: BsCurve) -> float:
    assert ReplaceValue(LeftCurve, Poles=(), Weights=()) == ReplaceValue(
        RightCurve, Poles=(), Weights=()
    )
    return max(
        PointSpread(LeftCurve.Poles, RightCurve.Poles),
        ValueSpread(LeftCurve.Weights, RightCurve.Weights),
    )


def ShiftCurve(Curve: BsCurve, ShiftU: float, ShiftV: float) -> BsCurve:
    return ReplaceValue(
        Curve,
        Poles=tuple(
            (PoleValue[0] + ShiftU, PoleValue[1] + ShiftV, *PoleValue[2:])
            for PoleValue in Curve.Poles
        ),
    )


def SeamSpread(LeftCurve: BsCurve, RightCurve: BsCurve, Cache: NubsSurface) -> float:
    SpanU = Cache.KnotsU[-1].Value - Cache.KnotsU[0].Value
    SpanV = Cache.KnotsV[-1].Value - Cache.KnotsV[0].Value
    StepsU = (-1, 0, 1) if Cache.ClosureU else (0,)
    StepsV = (-1, 0, 1) if Cache.ClosureV else (0,)
    return min(
        CurveSpread(ShiftCurve(LeftCurve, StepU * SpanU, StepV * SpanV), RightCurve)
        for StepU in StepsU
        for StepV in StepsV
    )


def WindowBox(Entry: FormWindow) -> tuple[float, ...]:
    return (Entry.ULow, Entry.UHigh, Entry.VLow, Entry.VHigh)


def BoundSpread(LeftEdge: FormEdge, RightEdge: FormEdge) -> float:
    if LeftEdge.Bounds is None or RightEdge.Bounds is None:
        assert LeftEdge.Bounds == RightEdge.Bounds
        return 0.0
    return ValueSpread(LeftEdge.Bounds, RightEdge.Bounds)


def EdgeSpread(LeftEdge: FormEdge, RightEdge: FormEdge) -> float:
    Plain = ReplaceValue(
        LeftEdge, Curve=RightEdge.Curve, Label="", Windows=(), Bounds=RightEdge.Bounds
    )
    assert Plain == ReplaceValue(RightEdge, Label="", Windows=())
    assert [Entry.Face for Entry in LeftEdge.Windows] == [
        Entry.Face for Entry in RightEdge.Windows
    ]
    Boxes = PointSpread(
        tuple(WindowBox(Entry) for Entry in LeftEdge.Windows),
        tuple(WindowBox(Entry) for Entry in RightEdge.Windows),
    )
    return max(
        Boxes,
        BoundSpread(LeftEdge, RightEdge),
        CurveSpread(LeftEdge.Curve, RightEdge.Curve),
    )


def FaceSpread(LeftFace: FormFace, RightFace: FormFace) -> float:
    LeftCache, RightCache = LeftFace.Surface.Cache, RightFace.Surface.Cache
    assert ReplaceValue(LeftCache, Points=(), Weights=()) == ReplaceValue(
        RightCache, Points=(), Weights=()
    )
    assert ReplaceValue(LeftFace.Surface, Cache=RightCache) == RightFace.Surface
    assert (LeftFace.DoubleSided, LeftFace.Contained) == (
        RightFace.DoubleSided,
        RightFace.Contained,
    )
    Spreads = [
        PointSpread(LeftCache.Points, RightCache.Points),
        ValueSpread(LeftCache.Weights, RightCache.Weights),
    ]
    for LeftUse, RightUse in zip(LeftFace.Uses, RightFace.Uses, strict=True):
        assert (LeftUse.EdgeIndex, LeftUse.Reversed) == (
            RightUse.EdgeIndex,
            RightUse.Reversed,
        )
        Spreads.append(SeamSpread(LeftUse.Pcurve, RightUse.Pcurve, RightCache))
        Spreads.append(abs(LeftUse.Fit - RightUse.Fit))
    return max(Spreads)


def BodySpread(Built: FormBody, Native: FormBody) -> float:
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
    "CaseValue", KGeneralCases + KCapCases, ids=lambda CaseValue: CaseValue[0]
)
def TestGeneralCase(CaseValue: tuple[str, ...]) -> None:
    Surface = ReadTspline(ReadFormFile(CaseValue[1], CaseValue[2]))
    Native = ReadConverted(ReadDocument(ReadFormFile(CaseValue[3], CaseValue[4])))
    assert BodySpread(ConvertForm(Surface), Native) <= KGeneralSlack


@KNeedZip
@MarkTests.parametrize("CaseValue", KCapCases, ids=lambda CaseValue: CaseValue[0])
def TestCapDeclFlow(CaseValue: tuple[str, ...]) -> None:
    Surface = ReadTspline(ReadFormFile(CaseValue[1], CaseValue[2]))
    Emitted = ReadDocument(
        EmitFormDoc(FormSpec("Kit " + CaseValue[0], Surface, ConvertForm(Surface)))
    )
    Native = ReadDocument(ReadFormFile(CaseValue[3], CaseValue[4]))
    assert Emitted.Forms[0].Surface.Header == Surface.Header
    assert Native.Forms[0].Surface.Header.CapType == "G1CAPS"
    assert (
        Native.Forms[0].Surface.Header.StarSmoothness == Surface.Header.StarSmoothness
    )


@KNeedZip
def TestCubeMass() -> None:
    Parts = BoxParts((1, 1, 1))
    Plain = MakeSurface(Parts)
    Surface = ReplaceValue(Plain, Creases=BoxCreases(Parts, Plain, 1.0))
    Converted = ConvertForm(Surface)
    Emitted = ReadDocument(
        EmitFormDoc(FormSpec("Kit analytic cube", Surface, Converted))
    )
    assert Emitted.Forms[0].Surface == Surface
    assert ReadConverted(Emitted) == Converted
    assert (len(Converted.PointsCm), len(Converted.Edges), len(Converted.Faces)) == (
        8,
        12,
        6,
    )
    Cached = MaterialFields(NamedGroups(Emitted, "Body")[0]["cache"])
    assert Cached["area"] == ApproxValue(6.0, rel=1e-8, abs=1e-8)
    assert Cached["volume"] == ApproxValue(1.0, rel=1e-8, abs=1e-8)
    assert ReadPoint(Cached["cog"]) == ApproxValue((0.5, 0.5, 0.5), rel=1e-8, abs=1e-8)
    assert ReadPoint(Cached["moi"]) == ApproxValue((2.0 / 3.0,) * 3, rel=1e-8, abs=1e-8)
    assert ReadPoint(Cached["moiOffDiag"]) == ApproxValue(
        (-0.25, -0.25, -0.25), rel=1e-8, abs=1e-8
    )


@KNeedZip
def TestShiftMass() -> None:
    BaseCase, ShiftedCase = (
        next(CaseValue for CaseValue in KCapCases if CaseValue[0] == CaseName)
        for CaseName in ("Box3Same", "Box3ShiftedG2")
    )
    BaseSurface = ReadTspline(ReadFormFile(BaseCase[1], BaseCase[2]))
    ShiftedSurface = ReadTspline(ReadFormFile(ShiftedCase[1], ShiftedCase[2]))
    BaseDoc = ReadDocument(
        EmitFormDoc(FormSpec("Kit Box3Same", BaseSurface, ConvertForm(BaseSurface)))
    )
    Shifted = ReadDocument(
        EmitFormDoc(
            FormSpec("Kit Box3ShiftedG2", ShiftedSurface, ConvertForm(ShiftedSurface))
        )
    )
    BaseCache = MaterialFields(NamedGroups(BaseDoc, "Body")[0]["cache"])
    ShiftedCache = MaterialFields(NamedGroups(Shifted, "Body")[0]["cache"])
    assert BaseCache["area"] == ApproxValue(ShiftedCache["area"], rel=1e-8, abs=1e-8)
    assert BaseCache["volume"] == ApproxValue(
        ShiftedCache["volume"], rel=1e-8, abs=1e-8
    )
    Center = ReadPoint(BaseCache["cog"])
    ShiftedCenter = ReadPoint(ShiftedCache["cog"])
    OffsetX, OffsetY, OffsetZ = 13.0, -21.0, 42.0
    assert ShiftedCenter == ApproxValue(
        (Center[0] + OffsetX, Center[1] + OffsetY, Center[2] + OffsetZ),
        rel=1e-8,
        abs=1e-8,
    )
    BaseMoi = ReadPoint(BaseCache["moi"])
    OffDiagonal = ReadPoint(BaseCache["moiOffDiag"])
    Volume = ReadScalar(BaseCache["volume"])
    ExpectedMoi = (
        BaseMoi[0]
        + Volume
        * (2 * Center[1] * OffsetY + OffsetY**2 + 2 * Center[2] * OffsetZ + OffsetZ**2),
        BaseMoi[1]
        + Volume
        * (2 * Center[0] * OffsetX + OffsetX**2 + 2 * Center[2] * OffsetZ + OffsetZ**2),
        BaseMoi[2]
        + Volume
        * (2 * Center[0] * OffsetX + OffsetX**2 + 2 * Center[1] * OffsetY + OffsetY**2),
    )
    ExpectedOffDiagonal = (
        OffDiagonal[0]
        - Volume * (Center[0] * OffsetY + Center[1] * OffsetX + OffsetX * OffsetY),
        OffDiagonal[1]
        - Volume * (Center[0] * OffsetZ + Center[2] * OffsetX + OffsetX * OffsetZ),
        OffDiagonal[2]
        - Volume * (Center[1] * OffsetZ + Center[2] * OffsetY + OffsetY * OffsetZ),
    )
    assert ReadPoint(ShiftedCache["moi"]) == ApproxValue(
        ExpectedMoi, rel=1e-8, abs=1e-8
    )
    assert ReadPoint(ShiftedCache["moiOffDiag"]) == ApproxValue(
        ExpectedOffDiagonal, rel=1e-8, abs=1e-8
    )


@KNeedZip
def TestPlanarArea() -> None:
    Native = ReadDocument(ReadFormFile(*KPlanarArea))
    Surface = Native.Forms[0].Surface
    Emitted = ReadDocument(
        EmitFormDoc(FormSpec("Kit planar area", Surface, ConvertForm(Surface)))
    )
    Cached = MaterialFields(NamedGroups(Emitted, "Body")[0]["cache"])
    Expected = MaterialFields(NamedGroups(Native, "Body")[0]["cache"])
    assert Cached["area"] == ApproxValue(Expected["area"], rel=1e-8, abs=1e-8)
