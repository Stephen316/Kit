import math
from fractions import Fraction

from convert.Formats.Fusion.BrepCodec.Journal.Spline.Caps.CapKnots import (
    KClamp,
    BasisDerive,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Caps.CapLayout import (
    KCapRow,
    KSpan,
    CapLayout,
    AddTermMut,
    CombineRows,
    EmptyRow,
    SurfaceRow,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import SpokeKey
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KPoleRow,
    MixRows,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Caps.RoundTrig import RoundCosine

# sample count needs one explicit bound so spline cap reconstruction cannot accept inconsistent resource or layout limits
KSampleCount = 5

# the cube steps order must stay explicit so extraordinary vertices remain compatible with surrounding patches
KCubeSteps = ((1.0, 3), (-3.0, 2), (3.0, 1), (-1.0, 0))

# the flex rows order must stay explicit so extraordinary vertices remain compatible with surrounding patches
KFlexRows = (2, 3)


# the profile weight contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def ProfileWeight(Ratio: Fraction) -> Fraction:
    if Ratio <= 1:
        return 1 - Fraction(2, 3) * Ratio
    if Ratio <= 2:
        return (2 - Ratio) ** 2 / 3
    return Fraction(0)


# the spoke samples contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def SpokeSamples(StepValue: Fraction) -> list[Fraction]:
    Found: list[Fraction] = []
    for Piece in (0, 1):
        Found += [
            StepValue * Piece + StepValue * Index / KSampleCount
            for Index in range(KSampleCount + 1)
        ]
    return Found


# the cap step contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def CapStep(Layout: CapLayout) -> Fraction:
    return Layout.KnotsI[0][KClamp]


# the smooth rows contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def SmoothRows(Layout: CapLayout) -> list[KCapRow]:
    StepValue = CapStep(Layout)
    Cosine = RoundCosine(2.0 * math.pi / Layout.Valence)
    Origin = Fraction(0)
    Found: list[KCapRow] = []
    for Sector in range(Layout.Valence):
        for Param in SpokeSamples(StepValue):
            Across = SurfaceRow(Layout, Sector, (Param, Origin), (0, 1))
            Before = SurfaceRow(Layout, Sector - 1, (Origin, Param), (1, 0))
            Along = SurfaceRow(Layout, Sector, (Param, Origin), (1, 0))
            Scale = 2.0 * Cosine * float(ProfileWeight(Param / StepValue))
            Found.append(CombineRows(((1.0, Across), (1.0, Before), (-Scale, Along))))
    return Found


# the spoke rows contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def SpokeRows(Layout: CapLayout) -> list[KCapRow]:
    StepValue = CapStep(Layout)
    Origin = Fraction(0)
    Found: list[KCapRow] = []
    for Sector in range(Layout.Valence):
        Parts = [
            (
                Scalar,
                SurfaceRow(
                    Layout, Sector, (StepValue + StepValue * Third / 3, Origin), (0, 0)
                ),
            )
            for Scalar, Third in KCubeSteps
        ]
        Found.append(CombineRows(Parts))
    return Found


# the flex row contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def FlexRow(Layout: CapLayout, Sector: int, AxisIndex: int, Other: int) -> KCapRow:
    Knots = (Layout.KnotsI if AxisIndex == 0 else Layout.KnotsJ)[Sector]
    EdgeValue = 2 * CapStep(Layout)
    After = BasisDerive(Knots, EdgeValue, 2, False)
    Prior = BasisDerive(Knots, EdgeValue, 2, True)
    Dense = EmptyRow(Layout)
    Moved: list[tuple[float, KPoleRow]] = []
    for Index in range(min(KSpan, len(After))):
        JumpValue = After[Index] - Prior[Index]
        if JumpValue:
            PlacePair = (Index, Other) if AxisIndex == 0 else (Other, Index)
            AddTermMut(
                Layout,
                (Dense, Moved),
                SpokeKey(Sector, Layout.Valence, *PlacePair),
                float(JumpValue),
            )
    return Dense, MixRows(Moved)


# the flex rows contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def FlexRows(Layout: CapLayout) -> list[KCapRow]:
    return [
        FlexRow(Layout, Sector, AxisIndex, Other)
        for Sector in range(Layout.Valence)
        for AxisIndex in (0, 1)
        for Other in KFlexRows
    ]


# the center row contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def CenterRow(Layout: CapLayout, Limit: KPoleRow) -> KCapRow:
    Dense = EmptyRow(Layout)
    Dense[Layout.Slots[("ep",)]] = 1.0
    return Dense, dict(Limit)


# the hard rows contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def HardRows(Layout: CapLayout, Limit: KPoleRow) -> list[KCapRow]:
    return [
        CenterRow(Layout, Limit),
        *SmoothRows(Layout),
        *SpokeRows(Layout),
        *FlexRows(Layout),
    ]
