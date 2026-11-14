from dataclasses import dataclass as MakeDataClass
from decimal import Decimal as ExactDecimal

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Notes.DimensionPlan import (
    KTextHeight,
)

KInchLength = ExactDecimal("25.4")
KTitleHeight = 2.5
KSwissPitch = 0x22
KFontFile = "Arial.ttf"
KFontFamily = "Arial"
KLineWeights = (0, 5, 9, 13, 15, 18, 20, 25, 30, 35, 40, 50, 53, 60, 70, 80)
KDefaultIndex = 31
KPlotBit = 0x10
KWeightShift = 5
KNarrowLine = 0.25
KTitleLine = 0.35
KWideLine = 0.5

KFixedHandles = (
    ("Control:BLOCK", 0x1),
    ("Control:LAYER", 0x2),
    ("Control:STYLE", 0x3),
    ("Control:LTYPE", 0x5),
    ("Control:VIEW", 0x6),
    ("Control:UCS", 0x7),
    ("Control:VPORT", 0x8),
    ("Control:APPID", 0x9),
    ("Control:DIMSTYLE", 0xA),
    ("NOD", 0xC),
    ("NOD/ACAD_GROUP", 0xD),
    ("NOD/ACAD_PLOTSTYLENAME", 0xE),
    ("NOD/ACAD_PLOTSTYLENAME/Normal", 0xF),
)


@MakeDataClass(frozen=True, slots=True)
class LayerSpec:
    EntryName: str
    Linetype: str
    LineWidth: float | None
    Plots: bool = True

    @property
    def LayerValues(self) -> int:
        Index = (
            KDefaultIndex
            if self.LineWidth is None
            else KLineWeights.index(round(self.LineWidth * 100))
        )
        return Index << KWeightShift | (KPlotBit if self.Plots else 0)


@MakeDataClass(frozen=True, slots=True)
class LinetypeSpec:
    EntryName: str
    Description: str
    InchDashes: tuple[float, ...]

    @property
    def Dashes(self) -> tuple[float, ...]:
        return tuple(float(Stroke) for Stroke in self.ExactDashes)

    @property
    def PatternLength(self) -> float:
        return sum(abs(Stroke) for Stroke in self.Dashes)

    @property
    def ExactDashes(self) -> tuple[ExactDecimal, ...]:
        return tuple(
            ExactDecimal(repr(Stroke)) * KInchLength for Stroke in self.InchDashes
        )


KLayerSpecs = (
    LayerSpec("0", "Continuous", None),
    LayerSpec("Defpoints", "Continuous", None, False),
    LayerSpec("Visible", "Continuous", KWideLine),
    LayerSpec("Hidden", "HIDDEN2", KNarrowLine),
    LayerSpec("Smart Centers", "CENTER2", KNarrowLine),
    LayerSpec("FD_Dimensions", "Continuous", KNarrowLine),
    LayerSpec("BORDER", "Continuous", KNarrowLine),
    LayerSpec("TITLEBLOCK", "Continuous", KTitleLine),
)

KLinetypeSpecs = (
    LinetypeSpec("ByBlock", "", ()),
    LinetypeSpec("ByLayer", "", ()),
    LinetypeSpec("Continuous", "Solid line", ()),
    LinetypeSpec(
        "CENTER2",
        "Center (.5x) ___ _ ___ _ ___ _ ___ _ ___ _ ___",
        (0.75, -0.125, 0.125, -0.125),
    ),
    LinetypeSpec(
        "HIDDEN2", "Hidden (.5x) _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _", (0.125, -0.0625)
    ),
    LinetypeSpec(
        "ACAD_VIEWBORDER_LINETYPE", "Dashed line in view border", (0.0625, -0.25)
    ),
)


KStyleSpecs = (("Standard", KTextHeight), ("FusionTitle", KTitleHeight))
