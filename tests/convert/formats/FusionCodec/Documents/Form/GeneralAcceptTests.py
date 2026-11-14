from dataclasses import replace as ReplaceValue
from sys import version_info as PythonVersion

from pytest import mark as MarkTests

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
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.convert.formats.FusionCodec.Documents.Form.GeneralCases import (
    KGeneralCases,
)
from tests.convert.formats.FusionCodec.Documents.Form.ReadConverted import (
    ReadConverted,
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
@MarkTests.parametrize("CaseValue", KGeneralCases, ids=lambda CaseValue: CaseValue[0])
def TestGeneralCase(CaseValue: tuple[str, str, str, str, str]) -> None:
    Surface = ReadTspline(ReadFormFile(CaseValue[1], CaseValue[2]))
    Native = ReadConverted(ReadDocument(ReadFormFile(CaseValue[3], CaseValue[4])))
    assert BodySpread(ConvertForm(Surface), Native) <= KGeneralSlack
