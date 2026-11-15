from dataclasses import dataclass as MakeDataClass
from math import isclose as IsClose

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Notes.TextMetrics import (
    MiddleOffset,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import (
    KAsmeMargin,
    KInchLength,
    PaperSize,
)

# the point pair shape must stay shared so drawing sheet authoring uses one contract for compatible values
KPointPair = tuple[float, float]

# the segment shape must stay shared so drawing sheet authoring uses one contract for compatible values
KSegment = tuple[KPointPair, KPointPair]

# zone step must remain consistent across callers so paper layouts retain consistent object ownership
KZoneStep = 100.0

# zone letters must remain consistent across callers so paper layouts retain consistent object ownership
KZoneLetters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# the asme sides order must stay explicit so paper layouts retain consistent object ownership
KAsmeSides = (8.5 * KInchLength, 11.0 * KInchLength)


# frame rule needs an explicit state contract so paper layouts retain consistent object ownership
@MakeDataClass(frozen=True, slots=True)
class FrameRule:
    FilingMargin: float
    BandWidth: float
    ZoneReach: float
    TrimMark: float
    LabelHeight: float
    CentreMarks: bool
    FromCorner: bool


# iso frame must remain consistent across callers so paper layouts retain consistent object ownership
KIsoFrame = FrameRule(20.0, 5.0, 5.0, 15.0, 2.5, True, False)

# asme frame must remain consistent across callers so paper layouts retain consistent object ownership
KAsmeFrame = FrameRule(
    KAsmeMargin,
    0.25 * KInchLength,
    KAsmeMargin,
    0.0,
    0.12 * KInchLength,
    False,
    True,
)


# zone label needs an explicit state contract so paper layouts retain consistent object ownership
@MakeDataClass(frozen=True, slots=True)
class ZoneLabel:
    TextValue: str
    Centre: KPointPair
    Insertion: KPointPair
    TextHeight: float


# border plan needs an explicit state contract so paper layouts retain consistent object ownership
@MakeDataClass(frozen=True, slots=True)
class BorderPlan:
    BlockName: str
    FrameLines: tuple[KSegment, ...]
    TrimLines: tuple[KSegment, ...]
    MarkLines: tuple[KSegment, ...]
    Labels: tuple[ZoneLabel, ...]


# frame box needs an explicit state contract so paper layouts retain consistent object ownership
@MakeDataClass(frozen=True, slots=True)
class FrameBox:
    LeftEdge: float
    RightEdge: float
    BottomEdge: float
    TopEdge: float
    ColumnCount: int
    RowCount: int
    Style: FrameRule

    # the middle x contract needs a shared interpretation so paper layouts retain consistent object ownership
    @property
    def MiddleX(self) -> float:
        return (self.LeftEdge + self.RightEdge) / 2

    # the middle y contract needs a shared interpretation so paper layouts retain consistent object ownership
    @property
    def MiddleY(self) -> float:
        return (self.BottomEdge + self.TopEdge) / 2

    # the step x contract needs a shared interpretation so paper layouts retain consistent object ownership
    @property
    def StepX(self) -> float:
        SpanLength = self.RightEdge - self.LeftEdge + 2 * self.Style.ZoneReach
        return SpanLength / self.ColumnCount

    # the step y contract needs a shared interpretation so paper layouts retain consistent object ownership
    @property
    def StepY(self) -> float:
        SpanLength = self.TopEdge - self.BottomEdge + 2 * self.Style.ZoneReach
        return SpanLength / self.RowCount


# the frame of contract needs a shared interpretation so paper layouts retain consistent object ownership
def FrameOf(Paper: PaperSize) -> FrameRule:
    return KIsoFrame if Paper.IsMetric else KAsmeFrame


# side zones needs an explicit validity boundary so paper layouts retain consistent object ownership
def SideZones(Length: float, Metric: bool) -> int:
    if Metric:
        return 2 * max(1, round(Length / KZoneStep))
    for SideLength in KAsmeSides:
        Doubling = Length / SideLength
        if IsClose(Doubling, round(Doubling)):
            return 2 * round(Doubling)
    raise ValueError(f"Authored DWG sheet side {Length!r} is not an ASME side")


# the zone counts contract needs a shared interpretation so paper layouts retain consistent object ownership
def ZoneCounts(Paper: PaperSize) -> tuple[int, int]:
    Across = SideZones(Paper.PaperWidth, Paper.IsMetric)
    return Across, SideZones(Paper.PaperHeight, Paper.IsMetric)


# the label operation needs a consistent construction rule so paper layouts retain consistent object ownership
def MakeLabel(TextValue: str, Middle: KPointPair, Height: float) -> ZoneLabel:
    Across, Upward = MiddleOffset(TextValue, Height)
    Corner = (Middle[0] - Across, Middle[1] - Upward)
    return ZoneLabel(TextValue, Middle, Corner, Height)


# the trim lines contract needs a shared interpretation so paper layouts retain consistent object ownership
def TrimLines(Width: float, Height: float, MarkLength: float) -> tuple[KSegment, ...]:
    Segments: list[KSegment] = []
    for CornerX, Inward in ((0.0, MarkLength), (Width, -MarkLength)):
        for CornerY, Upward in ((0.0, MarkLength), (Height, -MarkLength)):
            Segments.append(((CornerX, CornerY), (CornerX + Inward, CornerY)))
            Segments.append(((CornerX, CornerY), (CornerX, CornerY + Upward)))
    return tuple(Segments) if MarkLength else ()


# the frame lines contract needs a shared interpretation so paper layouts retain consistent object ownership
def FrameLines(Frame: FrameBox) -> tuple[KSegment, ...]:
    LeftEdge, RightEdge = Frame.LeftEdge, Frame.RightEdge
    BottomEdge, TopEdge = Frame.BottomEdge, Frame.TopEdge
    return (
        ((LeftEdge, BottomEdge), (RightEdge, BottomEdge)),
        ((RightEdge, BottomEdge), (RightEdge, TopEdge)),
        ((RightEdge, TopEdge), (LeftEdge, TopEdge)),
        ((LeftEdge, TopEdge), (LeftEdge, BottomEdge)),
    )


# the centre marks contract needs a shared interpretation so paper layouts retain consistent object ownership
def CentreMarks(Frame: FrameBox) -> list[KSegment]:
    BandWidth = Frame.Style.BandWidth
    MiddleX, MiddleY = Frame.MiddleX, Frame.MiddleY
    return [
        (
            (MiddleX, Frame.BottomEdge - BandWidth),
            (MiddleX, Frame.BottomEdge + BandWidth),
        ),
        ((MiddleX, Frame.TopEdge + BandWidth), (MiddleX, Frame.TopEdge - BandWidth)),
        ((Frame.LeftEdge - BandWidth, MiddleY), (Frame.LeftEdge + BandWidth, MiddleY)),
        (
            (Frame.RightEdge + BandWidth, MiddleY),
            (Frame.RightEdge - BandWidth, MiddleY),
        ),
    ]


# the divisions contract needs a shared interpretation so paper layouts retain consistent object ownership
def Divisions(Middle: float, StepSize: float, Count: int, Centred: bool) -> list[float]:
    Levels = [Middle] if not Centred else []
    for Index in range(1, Count // 2):
        Levels.extend((Middle - Index * StepSize, Middle + Index * StepSize))
    return Levels


# the mark lines contract needs a shared interpretation so paper layouts retain consistent object ownership
def MarkLines(Frame: FrameBox) -> tuple[KSegment, ...]:
    BandWidth, Centred = Frame.Style.BandWidth, Frame.Style.CentreMarks
    LeftEdge, RightEdge = Frame.LeftEdge, Frame.RightEdge
    BottomEdge, TopEdge = Frame.BottomEdge, Frame.TopEdge
    Marks = CentreMarks(Frame) if Centred else []
    for Across in Divisions(Frame.MiddleX, Frame.StepX, Frame.ColumnCount, Centred):
        Marks.append(((Across, BottomEdge - BandWidth), (Across, BottomEdge)))
        Marks.append(((Across, TopEdge + BandWidth), (Across, TopEdge)))
    for Upward in Divisions(Frame.MiddleY, Frame.StepY, Frame.RowCount, Centred):
        Marks.append(((LeftEdge - BandWidth, Upward), (LeftEdge, Upward)))
        Marks.append(((RightEdge + BandWidth, Upward), (RightEdge, Upward)))
    return tuple(Marks)


# the zone names contract needs a shared interpretation so paper layouts retain consistent object ownership
def ZoneNames(Frame: FrameBox) -> tuple[list[str], list[str]]:
    Numbers = [str(Index + 1) for Index in range(Frame.ColumnCount)]
    Letters = list(KZoneLetters[: Frame.RowCount])
    if Frame.Style.FromCorner:
        Numbers.reverse()
        Letters.reverse()
    return Numbers, Letters


# the zone labels contract needs a shared interpretation so paper layouts retain consistent object ownership
def ZoneLabels(Frame: FrameBox) -> tuple[ZoneLabel, ...]:
    BandWidth, Height = Frame.Style.BandWidth, Frame.Style.LabelHeight
    Numbers, Letters = ZoneNames(Frame)
    Labels: list[ZoneLabel] = []
    StartX = Frame.MiddleX - Frame.ColumnCount / 2 * Frame.StepX
    for Index, TextValue in enumerate(Numbers):
        Across = StartX + (Index + 0.5) * Frame.StepX
        for Upward in (Frame.BottomEdge - BandWidth / 2, Frame.TopEdge + BandWidth / 2):
            Labels.append(MakeLabel(TextValue, (Across, Upward), Height))
    StartY = Frame.MiddleY + Frame.RowCount / 2 * Frame.StepY
    for Index, TextValue in enumerate(Letters):
        Upward = StartY - (Index + 0.5) * Frame.StepY
        for Across in (Frame.LeftEdge - BandWidth / 2, Frame.RightEdge + BandWidth / 2):
            Labels.append(MakeLabel(TextValue, (Across, Upward), Height))
    return tuple(Labels)


# the plan border contract needs a stable decomposition so paper layouts retain consistent object ownership
def PlanBorder(Paper: PaperSize) -> BorderPlan:
    Width, Height, Margin = Paper.PaperWidth, Paper.PaperHeight, Paper.FrameMargin
    Style = FrameOf(Paper)
    ColumnTotal, RowTotal = ZoneCounts(Paper)
    Frame = FrameBox(
        Style.FilingMargin,
        Width - Margin,
        Margin,
        Height - Margin,
        ColumnTotal,
        RowTotal,
        Style,
    )
    if Frame.RowCount > len(KZoneLetters):
        raise ValueError(f"Authored DWG sheet needs {Frame.RowCount} zone letters")
    return BorderPlan(
        f"{Paper.StandardName}_{Paper.FormatName}_SHEET",
        FrameLines(Frame),
        TrimLines(Width, Height, Style.TrimMark),
        MarkLines(Frame),
        ZoneLabels(Frame),
    )
