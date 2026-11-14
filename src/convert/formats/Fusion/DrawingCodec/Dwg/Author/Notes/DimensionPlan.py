from dataclasses import dataclass as MakeDataClass
from math import atan2 as ArcTangent
from math import hypot as Hypotenuse

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Notes.TextMetrics import (
    TextExtent,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DimensionDraft import (
    KDimensionKinds,
    DimensionDraft,
)

KPointPair = tuple[float, float]
KSegment = tuple[KPointPair, KPointPair]
KArrow = tuple[KPointPair, KPointPair, KPointPair]
KLayout = tuple[KPointPair, tuple[KSegment, ...], tuple[KArrow, ...]]
KArrowSize = 3.5
KArrowRatio = 6.0
KExtOffset = 2.1
KExtExtend = 2.1
KTextGap = 1.4
KTextHeight = 3.5
KDecimals = 2
KTolerance = 1e-9


@MakeDataClass(frozen=True, slots=True)
class DimensionPlan:
    DimensionKind: str
    FirstPoint: KPointPair
    SecondPoint: KPointPair
    LinePoint: KPointPair
    TextPoint: KPointPair
    TextValue: str
    TextHeight: float
    TextWidth: float
    TextAngle: float
    Measurement: float
    LinearFactor: float
    LineAngle: float
    Lines: tuple[KSegment, ...]
    Arrows: tuple[KArrow, ...]
    Anchors: tuple[KPointPair, ...]


def MeasureText(Measurement: float) -> str:
    TextValue = f"{Measurement:.{KDecimals}f}".rstrip("0").rstrip(".")
    return "0" if TextValue in ("", "-0") else TextValue


def Shifted(Point: KPointPair, Toward: KPointPair, Length: float) -> KPointPair:
    return (Point[0] + Toward[0] * Length, Point[1] + Toward[1] * Length)


def DotPair(First: KPointPair, Second: KPointPair) -> float:
    return First[0] * Second[0] + First[1] * Second[1]


def UnitVector(Vector: KPointPair) -> KPointPair:
    Length = Hypotenuse(*Vector)
    if Length <= KTolerance:
        raise ValueError("Authored DWG dimension has coincident points")
    return (Vector[0] / Length, Vector[1] / Length)


def Normal(Vector: KPointPair) -> KPointPair:
    return (-Vector[1], Vector[0])


def ArrowAt(TipPoint: KPointPair, Inward: KPointPair, SideAxis: KPointPair) -> KArrow:
    BasePoint = Shifted(TipPoint, Inward, KArrowSize)
    Halved = KArrowSize / KArrowRatio
    return (
        Shifted(BasePoint, SideAxis, Halved),
        Shifted(BasePoint, SideAxis, -Halved),
        TipPoint,
    )


def ReadingAxis(DimAxis: KPointPair) -> KPointPair:
    if DimAxis[0] > KTolerance or (abs(DimAxis[0]) <= KTolerance and DimAxis[1] > 0):
        return DimAxis
    return (-DimAxis[0], -DimAxis[1])


def LinearAxis(Draft: DimensionDraft) -> tuple[KPointPair, KPointPair, KPointPair]:
    First, Second = Draft.FirstPoint, Draft.SecondPoint
    if Draft.DimensionKind == "Horizontal":
        DimAxis = (1.0, 0.0)
        return DimAxis, (First[0], Draft.LineHeight), (Second[0], Draft.LineHeight)
    if Draft.DimensionKind == "Vertical":
        DimAxis = (0.0, 1.0)
        return DimAxis, (Draft.LineHeight, First[1]), (Draft.LineHeight, Second[1])
    DimAxis = UnitVector((Second[0] - First[0], Second[1] - First[1]))
    SideAxis = Normal(DimAxis)
    return (
        DimAxis,
        Shifted(First, SideAxis, Draft.LineHeight),
        Shifted(Second, SideAxis, Draft.LineHeight),
    )


def ExtensionLine(Point: KPointPair, FootPoint: KPointPair) -> KSegment:
    Outward = UnitVector((FootPoint[0] - Point[0], FootPoint[1] - Point[1]))
    return (
        Shifted(Point, Outward, KExtOffset),
        Shifted(FootPoint, Outward, KExtExtend),
    )


def PlaceText(
    Middle: KPointPair, DimAxis: KPointPair, Height: float
) -> tuple[KPointPair, float]:
    Reading = ReadingAxis(DimAxis)
    Point = Shifted(Middle, Normal(Reading), KTextGap + Height / 2)
    return Point, ArcTangent(Reading[1], Reading[0])


def ExtensionLines(
    Pairs: tuple[tuple[KPointPair, KPointPair], ...],
) -> tuple[KSegment, ...]:
    Lines: list[KSegment] = []
    for Point, FootPoint in Pairs:
        Offset = Hypotenuse(FootPoint[0] - Point[0], FootPoint[1] - Point[1])
        if Offset <= KTolerance:
            continue
        if Offset <= KExtOffset:
            raise ValueError("Authored DWG dimension line overlaps its points")
        Lines.append(ExtensionLine(Point, FootPoint))
    return tuple(Lines)


def InsideLines(
    FootPair: KSegment, Toward: KPointPair, SideAxis: KPointPair
) -> KLayout:
    FirstFoot, SecondFoot = FootPair
    Backward = (-Toward[0], -Toward[1])
    Middle = ((FirstFoot[0] + SecondFoot[0]) / 2, (FirstFoot[1] + SecondFoot[1]) / 2)
    return (
        Middle,
        (
            (
                Shifted(FirstFoot, Toward, KArrowSize),
                Shifted(SecondFoot, Backward, KArrowSize),
            ),
        ),
        (
            ArrowAt(FirstFoot, Toward, SideAxis),
            ArrowAt(SecondFoot, Backward, SideAxis),
        ),
    )


def SplitLines(
    FootPair: KSegment, Toward: KPointPair, SideAxis: KPointPair, Width: float
) -> KLayout:
    FirstFoot, SecondFoot = FootPair
    Backward = (-Toward[0], -Toward[1])
    TextStart = KArrowSize + KTextGap
    return (
        Shifted(SecondFoot, Toward, TextStart + Width / 2),
        (
            (
                Shifted(FirstFoot, Toward, KArrowSize),
                Shifted(SecondFoot, Backward, KArrowSize),
            ),
            (SecondFoot, Shifted(SecondFoot, Toward, TextStart + Width + KTextGap)),
        ),
        (
            ArrowAt(FirstFoot, Toward, SideAxis),
            ArrowAt(SecondFoot, Backward, SideAxis),
        ),
    )


def OutsideLines(
    FootPair: KSegment, Toward: KPointPair, SideAxis: KPointPair, Width: float
) -> KLayout:
    FirstFoot, SecondFoot = FootPair
    Backward = (-Toward[0], -Toward[1])
    TextStart = 2 * KArrowSize + KTextGap
    return (
        Shifted(SecondFoot, Toward, TextStart + Width / 2),
        (
            (
                Shifted(FirstFoot, Backward, KArrowSize),
                Shifted(FirstFoot, Backward, 2 * KArrowSize),
            ),
            (
                Shifted(SecondFoot, Toward, KArrowSize),
                Shifted(SecondFoot, Toward, TextStart + Width + KTextGap),
            ),
            FootPair,
        ),
        (
            ArrowAt(FirstFoot, Backward, SideAxis),
            ArrowAt(SecondFoot, Toward, SideAxis),
        ),
    )


def FlankLines(FootPair: KSegment, Toward: KPointPair, SideAxis: KPointPair) -> KLayout:
    FirstFoot, SecondFoot = FootPair
    Backward = (-Toward[0], -Toward[1])
    Middle = ((FirstFoot[0] + SecondFoot[0]) / 2, (FirstFoot[1] + SecondFoot[1]) / 2)
    return (
        Middle,
        (
            (
                Shifted(FirstFoot, Backward, KArrowSize),
                Shifted(FirstFoot, Backward, 2 * KArrowSize),
            ),
            (
                Shifted(SecondFoot, Toward, KArrowSize),
                Shifted(SecondFoot, Toward, 2 * KArrowSize),
            ),
            FootPair,
        ),
        (
            ArrowAt(FirstFoot, Backward, SideAxis),
            ArrowAt(SecondFoot, Toward, SideAxis),
        ),
    )


def FitLayout(
    FootPair: KSegment,
    Toward: KPointPair,
    SideAxis: KPointPair,
    Width: float,
    SpanLength: float,
) -> KLayout:
    IsArrowFit = SpanLength >= 2 * KArrowSize + 2 * KTextGap
    IsTextFit = SpanLength >= Width + 2 * KTextGap
    if IsArrowFit and IsTextFit:
        return InsideLines(FootPair, Toward, SideAxis)
    if IsArrowFit:
        return SplitLines(FootPair, Toward, SideAxis, Width)
    if IsTextFit:
        return FlankLines(FootPair, Toward, SideAxis)
    return OutsideLines(FootPair, Toward, SideAxis, Width)


def LinearPlan(Draft: DimensionDraft) -> DimensionPlan:
    First, Second = Draft.FirstPoint, Draft.SecondPoint
    DimAxis, FirstFoot, SecondFoot = LinearAxis(Draft)
    SpanLength = DotPair((Second[0] - First[0], Second[1] - First[1]), DimAxis)
    if abs(SpanLength) <= KTolerance:
        raise ValueError("Authored DWG dimension has coincident points")
    Extensions = ExtensionLines(((First, FirstFoot), (Second, SecondFoot)))
    Toward = (
        DimAxis[0] if SpanLength > 0 else -DimAxis[0],
        DimAxis[1] if SpanLength > 0 else -DimAxis[1],
    )
    Measurement = abs(SpanLength) / Draft.ViewScale
    TextValue = MeasureText(Measurement)
    Height, Width = TextExtent(TextValue, KTextHeight)
    FootPair, SideAxis = (FirstFoot, SecondFoot), Normal(ReadingAxis(DimAxis))
    Middle, Lines, Arrows = FitLayout(
        FootPair, Toward, SideAxis, Width, abs(SpanLength)
    )
    Point, Angle = PlaceText(Middle, DimAxis, Height)
    return DimensionPlan(
        Draft.DimensionKind,
        First,
        Second,
        SecondFoot,
        Point,
        TextValue,
        Height,
        Width,
        Angle,
        Measurement,
        -1 / Draft.ViewScale,
        ArcTangent(DimAxis[1], DimAxis[0]),
        (*Extensions, *Lines),
        Arrows,
        (First, Second, SecondFoot),
    )


def RoundPlan(Draft: DimensionDraft) -> DimensionPlan:
    First, Second = Draft.FirstPoint, Draft.SecondPoint
    Outward = UnitVector((Second[0] - First[0], Second[1] - First[1]))
    Chord = Hypotenuse(Second[0] - First[0], Second[1] - First[1])
    IsRadius = Draft.DimensionKind == "Radius"
    Measurement = Chord / Draft.ViewScale
    Prefix = "R" if IsRadius else "∅"
    TextValue = Prefix + MeasureText(Measurement)
    if Draft.LineHeight <= KArrowSize:
        raise ValueError("Authored DWG round dimension leader is too short")
    Elbow = Shifted(Second, Outward, Draft.LineHeight)
    Height, Width = TextExtent(TextValue, KTextHeight)
    Reading = (1.0, 0.0) if Outward[0] >= 0 else (-1.0, 0.0)
    Shelf = Shifted(Elbow, Reading, Width + KTextGap)
    Middle = Shifted(Elbow, Reading, KTextGap / 2 + Width / 2)
    Point = (Middle[0], Middle[1] + KTextGap + Height / 2)
    Start = First if IsRadius else Shifted(First, Outward, KArrowSize)
    Inward = (-Outward[0], -Outward[1])
    Arrows: tuple[KArrow, ...] = (ArrowAt(Second, Inward, Normal(Outward)),)
    if not IsRadius:
        Arrows = (*Arrows, ArrowAt(First, Outward, Normal(Outward)))
    return DimensionPlan(
        Draft.DimensionKind,
        First,
        Second,
        Second,
        Point,
        TextValue,
        Height,
        Width,
        0.0,
        Measurement,
        -1 / Draft.ViewScale,
        ArcTangent(Outward[1], Outward[0]),
        ((Start, Shifted(Second, Inward, KArrowSize)), (Second, Elbow), (Elbow, Shelf)),
        Arrows,
        (First, Second),
    )


def PlanDimension(Draft: DimensionDraft) -> DimensionPlan:
    if Draft.DimensionKind not in KDimensionKinds:
        raise ValueError(
            f"Authored DWG dimension kind {Draft.DimensionKind!r} is unsupported"
        )
    if Draft.ViewScale <= 0:
        raise ValueError("Authored DWG dimension has no view scale")
    if Draft.DimensionKind in ("Radius", "Diameter"):
        return RoundPlan(Draft)
    return LinearPlan(Draft)
