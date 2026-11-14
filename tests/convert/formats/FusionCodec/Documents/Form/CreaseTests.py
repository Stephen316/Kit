from dataclasses import replace as ReplaceValue
from sys import version_info as PythonVersion

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.OrderJumps import (
    SpreadKnots,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import (
    ConvertForm,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import FormBody
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageBody import (
    CageBody,
    ShapeBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ClassifyEdges import (
    ClassifyEdges,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.SplineFrame import (
    CurveFrame,
    SurfaceFrame,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.SwapFormCage import (
    SwapFormCage,
)
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from tests.convert.formats.FusionCodec.Documents.Form.CreaseBodies import (
    FoldBody,
    PolePlaces,
)
from tests.convert.formats.FusionCodec.Documents.Form.CreaseFiles import (
    KCreaseBent,
    KCreaseCarrier,
    KCreaseOracle,
    KCreaseSplit,
    KCutCage,
)
from tests.convert.formats.FusionCodec.Documents.Form.ReadConverted import (
    ReadConverted,
)
from tests.convert.formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)

KFrameSlack = 1e-12
KFrameKnots = ((0.0, 3), (0.25, 2), (1.0, 1), (1.75, 2), (2.0, 3))
KFrameParams = (0.0, 0.1, 0.25, 0.6, 1.0, 1.3, 1.75, 1.9, 2.0)
KNeedZip = MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)
KRampPlaces = PolePlaces(6)
KLimitFolds = (
    (0.5, "tangent"),
    (0.9, "tangent"),
    (0.999, "tangent"),
    (-0.999, "tangent"),
    (1.001, "unknown"),
    (1.1, "unknown"),
    (-1.001, "unknown"),
    (2.0, "unknown"),
)
KSplitFault = "may split or reclassify"
KCreasePiece = tuple[tuple[float, float] | None, str]


def SpreadOrder(Knots: tuple[tuple[float, int], ...]) -> list[float]:
    return SpreadKnots(
        tuple(KnotValue for KnotValue, _ in Knots),
        tuple(Count for _, Count in Knots),
    )


def Greville(Knots: tuple[tuple[float, int], ...]) -> list[float]:
    Spread = SpreadOrder(Knots)
    return [
        sum(Spread[Index + 1 : Index + 4]) / 3.0 for Index in range(len(Spread) - 4)
    ]


def FoldPieces(
    Angles: tuple[float, ...], Splits: tuple[float, ...] = ()
) -> list[KCreasePiece]:
    Classified = ClassifyEdges(FoldBody(Angles, Splits))
    Pieces = [(EdgeValue.Bounds, EdgeValue.Convexity) for EdgeValue in Classified.Edges]
    return sorted(Pieces, key=lambda Piece: Piece[0] or (0.0, 0.0))


def FoldClasses(Angles: tuple[float, ...], Splits: tuple[float, ...] = ()) -> list[str]:
    return [Label for _, Label in FoldPieces(Angles, Splits)]


def EdgeClasses(BodyValue: FormBody) -> list[str]:
    return [EdgeValue.Convexity for EdgeValue in BodyValue.Edges]


def SplitSpread(Built: FormBody, Native: FormBody) -> float:
    Spreads = [
        abs(LeftValue - RightValue)
        for LeftPoint, RightPoint in zip(Built.PointsCm, Native.PointsCm, strict=True)
        for LeftValue, RightValue in zip(LeftPoint, RightPoint, strict=True)
    ]
    for LeftEdge, RightEdge in zip(Built.Edges, Native.Edges, strict=True):
        assert (LeftEdge.Bounds is None) == (RightEdge.Bounds is None)
        if LeftEdge.Bounds and RightEdge.Bounds:
            Spreads += [
                abs(LeftValue - RightValue)
                for LeftValue, RightValue in zip(LeftEdge.Bounds, RightEdge.Bounds)
            ]
    return max(Spreads)


def RampAngles(Slope: float, RootPlace: float) -> tuple[float, ...]:
    return tuple(Slope * (Place - RootPlace) for Place in KRampPlaces)


def MoveGrip(
    Surface: TsplineSurface, GripIndex: int, Shift: tuple[float, float, float]
) -> TsplineSurface:
    Grips = tuple(
        (
            ReplaceValue(
                GripValue,
                CoordX=GripValue.CoordX + Shift[0],
                CoordY=GripValue.CoordY + Shift[1],
                CoordZ=GripValue.CoordZ + Shift[2],
            )
            if Index == GripIndex
            else GripValue
        )
        for Index, GripValue in enumerate(Surface.Grips)
    )
    return ReplaceValue(Surface, Grips=Grips)


def TestCurveFrame() -> None:
    Places = Greville(KFrameKnots)
    Curve = BsCurve(
        False,
        3,
        0,
        tuple(KnotValue for KnotValue, _ in KFrameKnots),
        tuple(Count for _, Count in KFrameKnots),
        2,
        tuple((Place, 5.0) for Place in Places),
        (),
    )
    for Param in KFrameParams:
        Point, Tangent = CurveFrame(Curve, Param)
        assert abs(Point[0] - Param) <= KFrameSlack
        assert abs(Point[1] - 5.0) <= KFrameSlack
        assert abs(Tangent[0] - 1.0) <= KFrameSlack
        assert abs(Tangent[1]) <= KFrameSlack


def TestSurfaceAxes() -> None:
    Places = Greville(KFrameKnots)
    Knots = tuple(SplineKnot(KnotValue, Count) for KnotValue, Count in KFrameKnots)
    Points = tuple(
        (PlaceU, PlaceV, PlaceU * PlaceV) for PlaceV in Places for PlaceU in Places
    )
    Surface = NubsSurface(3, 3, 0, 0, 0, 0, Knots, Knots, Points)
    for ParamU in KFrameParams:
        for ParamV in KFrameParams:
            AlongU, AlongV = SurfaceFrame(Surface, ParamU, ParamV)
            Expected = ((1.0, 0.0, ParamV), (0.0, 1.0, ParamU))
            for Found, Wanted in zip((AlongU, AlongV), Expected, strict=True):
                assert max(
                    abs(First - Second) for First, Second in zip(Found, Wanted)
                ) <= (KFrameSlack)


@KNeedZip
def TestCreaseClass() -> None:
    Model = ReadDocument(ReadFormFile(*KCreaseCarrier))
    Carrier = Model.Forms[0].Surface
    Native = EdgeClasses(ReadConverted(Model))
    Built, Shaped = CageBody(Carrier), ShapeBody(Carrier)
    assert EdgeClasses(Built) == Native
    assert set(EdgeClasses(Shaped)) == {"unknown"}
    Unlabeled = tuple(
        ReplaceValue(EdgeValue, Convexity="unknown") for EdgeValue in Built.Edges
    )
    assert ReplaceValue(Built, Edges=Unlabeled) == Shaped
    BentCage = ReadTspline(ReadFormFile(*KCreaseBent))
    Classes = EdgeClasses(CageBody(BentCage))
    assert Native.count("unknown") + 1 == Classes.count("unknown")
    Oracle = ReadConverted(ReadDocument(ReadFormFile(*KCreaseOracle)))
    assert EdgeClasses(Oracle) == Classes


@KNeedZip
def TestCreaseFault() -> None:
    Model = ReadDocument(ReadFormFile(*KCreaseCarrier))
    SplitModel = ReadDocument(ReadFormFile(*KCreaseSplit))
    Split = SplitModel.Forms[0].Surface
    Built, Native = ConvertForm(Split), ReadConverted(SplitModel)
    assert len(Built.Edges) == len(ShapeBody(Split).Edges) + 1
    assert EdgeClasses(Built) == EdgeClasses(Native)
    assert SplitSpread(Built, Native) <= KFrameSlack
    with RaisesError(ValueError, match="change a crease edge class"):
        _ = SwapFormCage(Model, Split)
    BentCage = ReadTspline(ReadFormFile(*KCreaseBent))
    with RaisesError(ValueError, match="change a crease edge class"):
        _ = SwapFormCage(Model, BentCage)
    CutCage = ReadTspline(ReadFormFile(*KCutCage))
    with RaisesError(ValueError, match=KSplitFault):
        _ = ConvertForm(CutCage)


@KNeedZip
def TestCreaseGap() -> None:
    Model = ReadDocument(ReadFormFile(*KCreaseCarrier))
    Carrier = Model.Forms[0].Surface
    Native = EdgeClasses(ReadConverted(Model))
    Gentle = MoveGrip(Carrier, 31, (0.4, 0.0, 0.0))
    assert EdgeClasses(CageBody(Gentle)) == Native
    Raised = MoveGrip(Carrier, 31, (0.0, 0.0, 0.01))
    Classes = EdgeClasses(CageBody(Raised))
    assert Native.count("unknown") + 1 == Classes.count("unknown")


def TestCreaseLimit() -> None:
    for Angle, Label in KLimitFolds:
        assert FoldClasses((Angle,) * 7) == [Label]
        with RaisesError(ValueError, match=KSplitFault):
            _ = FoldClasses((Angle,) * 7, (2.0,))
    assert FoldClasses(RampAngles(0.999 / 6.0, 0.0)) == ["tangent"]
    assert FoldClasses(RampAngles(1.0006 / 6.0, 0.0)) == ["unknown"]


def TestFlatKnots() -> None:
    Steep = RampAngles(1.0, 3.0)
    assert FoldClasses(Steep, (3.0,)) == ["unknown", "unknown"]
    Gentle = RampAngles(0.2, 3.0)
    assert FoldClasses(Gentle) == ["tangent"]
    Stepped = (0.0,) * 5 + (2.0,) * 4
    assert FoldClasses(Stepped, (2.0,)) == ["tangent", "unknown"]
    Valley = (2.0, 2.0, 1.0, 0.0, 0.0, 0.0, 1.0, 2.0, 2.0)
    assert FoldClasses(Valley, (3.0,)) == ["unknown", "unknown"]
    Mixed = (0.6, 0.6, 0.3, 0.0, 0.0, 0.0, 1.0, 2.0, 2.0)
    assert FoldClasses(Mixed, (3.0,)) == ["tangent", "unknown"]
    for Angles, Place in ((Steep, 3.0), (Stepped, 2.0), (Valley, 3.0), (Mixed, 3.0)):
        assert FoldPieces(Angles) == FoldPieces(Angles, (Place,))
    for Angles, Splits in ((Gentle, (3.0,)), (Stepped, (1.0,))):
        with RaisesError(ValueError, match=KSplitFault):
            _ = FoldClasses(Angles, Splits)


def TestTurnRoots() -> None:
    assert FoldClasses(RampAngles(0.5, 1.4)) == ["unknown"]
    Crossed = RampAngles(1.0, 2.5)
    assert FoldPieces(Crossed) == [((0.0, 2.5), "unknown"), ((2.5, 6.0), "unknown")]
    with RaisesError(ValueError, match=KSplitFault):
        _ = FoldClasses(Crossed, (2.5,))
    Tilted = (-0.3, -0.3, -0.3, -0.3, 0.0, 0.3, 1.5, 2.5, 3.0)
    assert FoldPieces(Tilted) == [((0.0, 3.0), "tangent"), ((3.0, 6.0), "unknown")]
    assert FoldPieces(Tilted, (3.0,)) == FoldPieces(Tilted)
