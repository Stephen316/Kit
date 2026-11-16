from dataclasses import dataclass as MakeDataClass
from math import atan2 as ArcTangent
from math import hypot as Hypotenuse

from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Notes.TextMetrics import (
    TextExtent,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Spec.DimensionDraft import (
    KDimensionKinds,
    DimensionDraft,
)

# the point pair shape must stay shared so drawing annotation authoring uses one contract for compatible values
KPointPair = tuple[float, float]

# the segment shape must stay shared so drawing annotation authoring uses one contract for compatible values
KSegment = tuple[KPointPair, KPointPair]

# the arrow shape must stay shared so drawing annotation authoring uses one contract for compatible values
KArrow = tuple[KPointPair, KPointPair, KPointPair]

# the layout shape must stay shared so drawing annotation authoring uses one contract for compatible values
KLayout = tuple[KPointPair, tuple[KSegment, ...], tuple[KArrow, ...]]

# arrow size needs one explicit bound so drawing annotation authoring cannot accept inconsistent resource or layout limits
KArrowSize = 3.5

# arrow ratio must remain consistent across callers so annotation objects retain their layout ownership
KArrowRatio = 6.0

# ext offset must remain consistent across callers so annotation objects retain their layout ownership
KExtOffset = 2.1

# ext extend must remain consistent across callers so annotation objects retain their layout ownership
KExtExtend = 2.1

# text gap must remain consistent across callers so annotation objects retain their layout ownership
KTextGap = 1.4

# text height must remain consistent across callers so annotation objects retain their layout ownership
KTextHeight = 3.5

# decimals must remain consistent across callers so annotation objects retain their layout ownership
KDecimals = 2

# the tolerance tolerance prevents rounding noise from creating false geometric distinctions during reconstruction
KTolerance = 1e-9


# dimension plan needs an explicit state contract so annotation objects retain their layout ownership
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


# the measure text contract needs a shared interpretation so annotation objects retain their layout ownership
def MeasureText(Measurement: float) -> str:
    TextValue = f"{Measurement:.{KDecimals}f}".rstrip("0").rstrip(".")
    return "0" if TextValue in ("", "-0") else TextValue


# the shifted contract needs a shared interpretation so annotation objects retain their layout ownership
def Shifted(Point: KPointPair, Toward: KPointPair, Length: float) -> KPointPair:
    return (Point[0] + Toward[0] * Length, Point[1] + Toward[1] * Length)


# the pair operation needs one geometric convention so annotation objects retain their layout ownership
def DotPair(First: KPointPair, Second: KPointPair) -> float:
    return First[0] * Second[0] + First[1] * Second[1]


# the vector operation needs one geometric convention so annotation objects retain their layout ownership
def UnitVector(Vector: KPointPair) -> KPointPair:
    Length = Hypotenuse(*Vector)
    if Length <= KTolerance:
        raise ValueError("Authored DWG dimension has coincident points")
    return (Vector[0] / Length, Vector[1] / Length)


# normal needs one geometric convention so annotation objects retain their layout ownership
def Normal(Vector: KPointPair) -> KPointPair:
    return (-Vector[1], Vector[0])


# the arrow at contract needs a shared interpretation so annotation objects retain their layout ownership
def ArrowAt(TipPoint: KPointPair, Inward: KPointPair, SideAxis: KPointPair) -> KArrow:
    BasePoint = Shifted(TipPoint, Inward, KArrowSize)
    Halved = KArrowSize / KArrowRatio
    return (
        Shifted(BasePoint, SideAxis, Halved),
        Shifted(BasePoint, SideAxis, -Halved),
        TipPoint,
    )


# the reading axis contract needs a distinct decoding boundary so annotation objects retain their layout ownership
def ReadingAxis(DimAxis: KPointPair) -> KPointPair:
    if DimAxis[0] > KTolerance or (abs(DimAxis[0]) <= KTolerance and DimAxis[1] > 0):
        return DimAxis
    return (-DimAxis[0], -DimAxis[1])


# the linear axis contract needs a shared interpretation so annotation objects retain their layout ownership
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


# the extension line contract needs a shared interpretation so annotation objects retain their layout ownership
def ExtensionLine(Point: KPointPair, FootPoint: KPointPair) -> KSegment:
    Outward = UnitVector((FootPoint[0] - Point[0], FootPoint[1] - Point[1]))
    return (
        Shifted(Point, Outward, KExtOffset),
        Shifted(FootPoint, Outward, KExtExtend),
    )


# the text operation needs a consistent construction rule so annotation objects retain their layout ownership
def PlaceText(
    Middle: KPointPair, DimAxis: KPointPair, Height: float
) -> tuple[KPointPair, float]:
    Reading = ReadingAxis(DimAxis)
    Point = Shifted(Middle, Normal(Reading), KTextGap + Height / 2)
    return Point, ArcTangent(Reading[1], Reading[0])


# extension lines needs an explicit validity boundary so annotation objects retain their layout ownership
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


# the inside lines contract needs a shared interpretation so annotation objects retain their layout ownership
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


# the split lines contract needs a stable decomposition so annotation objects retain their layout ownership
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


# the outside lines contract needs a shared interpretation so annotation objects retain their layout ownership
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


# the flank lines contract needs a shared interpretation so annotation objects retain their layout ownership
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


# the fit layout contract needs a shared interpretation so annotation objects retain their layout ownership
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


# linear plan needs an explicit validity boundary so annotation objects retain their layout ownership
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


# round plan needs an explicit validity boundary so annotation objects retain their layout ownership
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


# the plan dimension contract needs a stable decomposition so annotation objects retain their layout ownership
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
