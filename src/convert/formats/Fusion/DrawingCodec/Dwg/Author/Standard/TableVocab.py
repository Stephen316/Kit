from dataclasses import dataclass as MakeDataClass
from decimal import Decimal as ExactDecimal

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Notes.DimensionPlan import (
    KTextHeight,
)

# inch length needs one explicit bound so drawing standard authoring cannot accept inconsistent resource or layout limits
KInchLength = ExactDecimal("25.4")

# title height must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KTitleHeight = 2.5

# swiss pitch must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KSwissPitch = 0x22

# font file must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KFontFile = "Arial.ttf"

# font family must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KFontFamily = "Arial"

# the line weights order must stay explicit so native drawing objects use a consistent symbol vocabulary
KLineWeights = (0, 5, 9, 13, 15, 18, 20, 25, 30, 35, 40, 50, 53, 60, 70, 80)

# default index must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KDefaultIndex = 31

# plot bit must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KPlotBit = 0x10

# weight shift must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KWeightShift = 5

# narrow line must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KNarrowLine = 0.25

# title line must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KTitleLine = 0.35

# wide line must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KWideLine = 0.5

# the fixed handles order must stay explicit so native drawing objects use a consistent symbol vocabulary
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


# layer specification needs an explicit state contract so native drawing objects use a consistent symbol vocabulary
@MakeDataClass(frozen=True, slots=True)
class LayerSpec:
    EntryName: str
    Linetype: str
    LineWidth: float | None
    Plots: bool = True

    # the layer values contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
    @property
    def LayerValues(self) -> int:
        Index = (
            KDefaultIndex
            if self.LineWidth is None
            else KLineWeights.index(round(self.LineWidth * 100))
        )
        return Index << KWeightShift | (KPlotBit if self.Plots else 0)


# linetype specification needs an explicit state contract so native drawing objects use a consistent symbol vocabulary
@MakeDataClass(frozen=True, slots=True)
class LinetypeSpec:
    EntryName: str
    Description: str
    InchDashes: tuple[float, ...]

    # the dashes contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
    @property
    def Dashes(self) -> tuple[float, ...]:
        return tuple(float(Stroke) for Stroke in self.ExactDashes)

    # the pattern length contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
    @property
    def PatternLength(self) -> float:
        return sum(abs(Stroke) for Stroke in self.Dashes)

    # the exact dashes contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
    @property
    def ExactDashes(self) -> tuple[ExactDecimal, ...]:
        return tuple(
            ExactDecimal(repr(Stroke)) * KInchLength for Stroke in self.InchDashes
        )


# the layer specifications order must stay explicit so native drawing objects use a consistent symbol vocabulary
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

# the linetype specifications order must stay explicit so native drawing objects use a consistent symbol vocabulary
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


# the style specifications order must stay explicit so native drawing objects use a consistent symbol vocabulary
KStyleSpecs = (("Standard", KTextHeight), ("FusionTitle", KTitleHeight))
