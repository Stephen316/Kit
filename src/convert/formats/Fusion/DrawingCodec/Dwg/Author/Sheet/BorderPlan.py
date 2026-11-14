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

KPointPair = tuple[float, float]
KSegment = tuple[KPointPair, KPointPair]
KZoneStep = 100.0
KZoneLetters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
KAsmeSides = (8.5 * KInchLength, 11.0 * KInchLength)


@MakeDataClass(frozen=True, slots=True)
class FrameRule:
    FilingMargin: float
    BandWidth: float
    ZoneReach: float
    TrimMark: float
    LabelHeight: float
    CentreMarks: bool
    FromCorner: bool


KIsoFrame = FrameRule(20.0, 5.0, 5.0, 15.0, 2.5, True, False)
KAsmeFrame = FrameRule(
    KAsmeMargin,
    0.25 * KInchLength,
    KAsmeMargin,
    0.0,
    0.12 * KInchLength,
    False,
    True,
)


@MakeDataClass(frozen=True, slots=True)
class ZoneLabel:
    TextValue: str
    Centre: KPointPair
    Insertion: KPointPair
    TextHeight: float


@MakeDataClass(frozen=True, slots=True)
class BorderPlan:
    BlockName: str
    FrameLines: tuple[KSegment, ...]
    TrimLines: tuple[KSegment, ...]
    MarkLines: tuple[KSegment, ...]
    Labels: tuple[ZoneLabel, ...]


@MakeDataClass(frozen=True, slots=True)
class FrameBox:
    LeftEdge: float
    RightEdge: float
    BottomEdge: float
    TopEdge: float
    ColumnCount: int
    RowCount: int
    Style: FrameRule

    @property
    def MiddleX(self) -> float:
        return (self.LeftEdge + self.RightEdge) / 2

    @property
    def MiddleY(self) -> float:
        return (self.BottomEdge + self.TopEdge) / 2

    @property
    def StepX(self) -> float:
        SpanLength = self.RightEdge - self.LeftEdge + 2 * self.Style.ZoneReach
        return SpanLength / self.ColumnCount

    @property
    def StepY(self) -> float:
        SpanLength = self.TopEdge - self.BottomEdge + 2 * self.Style.ZoneReach
        return SpanLength / self.RowCount


def FrameOf(Paper: PaperSize) -> FrameRule:
    return KIsoFrame if Paper.IsMetric else KAsmeFrame


def SideZones(Length: float, Metric: bool) -> int:
    if Metric:
        return 2 * max(1, round(Length / KZoneStep))
    for SideLength in KAsmeSides:
        Doubling = Length / SideLength
        if IsClose(Doubling, round(Doubling)):
            return 2 * round(Doubling)
    raise ValueError(f"Authored DWG sheet side {Length!r} is not an ASME side")


def ZoneCounts(Paper: PaperSize) -> tuple[int, int]:
    Across = SideZones(Paper.PaperWidth, Paper.IsMetric)
    return Across, SideZones(Paper.PaperHeight, Paper.IsMetric)


def MakeLabel(TextValue: str, Middle: KPointPair, Height: float) -> ZoneLabel:
    Across, Upward = MiddleOffset(TextValue, Height)
    Corner = (Middle[0] - Across, Middle[1] - Upward)
    return ZoneLabel(TextValue, Middle, Corner, Height)


def TrimLines(Width: float, Height: float, MarkLength: float) -> tuple[KSegment, ...]:
    Segments: list[KSegment] = []
    for CornerX, Inward in ((0.0, MarkLength), (Width, -MarkLength)):
        for CornerY, Upward in ((0.0, MarkLength), (Height, -MarkLength)):
            Segments.append(((CornerX, CornerY), (CornerX + Inward, CornerY)))
            Segments.append(((CornerX, CornerY), (CornerX, CornerY + Upward)))
    return tuple(Segments) if MarkLength else ()


def FrameLines(Frame: FrameBox) -> tuple[KSegment, ...]:
    LeftEdge, RightEdge = Frame.LeftEdge, Frame.RightEdge
    BottomEdge, TopEdge = Frame.BottomEdge, Frame.TopEdge
    return (
        ((LeftEdge, BottomEdge), (RightEdge, BottomEdge)),
        ((RightEdge, BottomEdge), (RightEdge, TopEdge)),
        ((RightEdge, TopEdge), (LeftEdge, TopEdge)),
        ((LeftEdge, TopEdge), (LeftEdge, BottomEdge)),
    )


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


def Divisions(Middle: float, StepSize: float, Count: int, Centred: bool) -> list[float]:
    Levels = [Middle] if not Centred else []
    for Index in range(1, Count // 2):
        Levels.extend((Middle - Index * StepSize, Middle + Index * StepSize))
    return Levels


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


def ZoneNames(Frame: FrameBox) -> tuple[list[str], list[str]]:
    Numbers = [str(Index + 1) for Index in range(Frame.ColumnCount)]
    Letters = list(KZoneLetters[: Frame.RowCount])
    if Frame.Style.FromCorner:
        Numbers.reverse()
        Letters.reverse()
    return Numbers, Letters


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
