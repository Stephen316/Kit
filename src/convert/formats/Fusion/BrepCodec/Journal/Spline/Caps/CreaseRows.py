import math
from dataclasses import replace as ReplaceFields
from fractions import Fraction

from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.CapLayout import (
    KCapRow,
    CapLayout,
    CombineRows,
    DeltaRow,
    EmptyRow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.HardRows import (
    CenterRow,
    FlexRows,
    SmoothRows,
    SpokeRows,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.RingRows import (
    RingRows,
    TangentRows,
    TwistRows,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.WindowRows import (
    KWindowRows,
    WindowRows,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import KCapKey
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KPoleRow,
    MixRows,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.RoundTrig import (
    RoundCosine,
    RoundSine,
)

KEvenWindow = 5
KOddWindow = 6
KPinReach = 4
KDartValence = 4
KCreaseRatio = Fraction(2, 3)
KWedgeTerms: tuple[tuple[str, int, int, Fraction, Fraction], ...] = (
    ("S", 0, 1, Fraction(0), Fraction(-1, 40)),
    ("S", 0, 2, Fraction(3, 160), Fraction(1, 20)),
    ("S", 0, 3, Fraction(-3, 32), Fraction(1, 20)),
    ("A", 1, 2, Fraction(-3, 160), Fraction(3, 20)),
    ("A", 1, 3, Fraction(3, 32), Fraction(0)),
    ("A", 2, 2, Fraction(0), Fraction(-4, 5)),
    ("A", 3, 2, Fraction(0), Fraction(1)),
)
KTripleOdd = (Fraction(-102, 5), Fraction(13, 10), Fraction(-1, 5))


def CreaseSpoke(Creased: tuple[bool, ...]) -> int:
    Spokes = [Spoke for Spoke, IsCrease in enumerate(Creased) if IsCrease]
    if len(Spokes) != 1 or len(Creased) == KDartValence:
        raise ValueError(
            "Fusion Form crease cap rule covers one creased spoke at an extraordinary point"
        )
    return Spokes[0]


def SectorKey(Layout: CapLayout, Sector: int, IndexI: int, IndexJ: int) -> KCapKey:
    return ("in", Sector % Layout.Valence, IndexI, IndexJ)


def NetRow(Layout: CapLayout, CapKey: KCapKey) -> KPoleRow:
    return Layout.Netref[Layout.Slots[CapKey]]


def KeptHard(Layout: CapLayout, Limit: KPoleRow, Spoke: int) -> list[KCapRow]:
    Smooth = SmoothRows(Layout)
    Block = len(Smooth) // Layout.Valence
    Quads = SpokeRows(Layout)
    return [
        CenterRow(Layout, Limit),
        *(RowValue for Index, RowValue in enumerate(Smooth) if Index // Block != Spoke),
        *(RowValue for Index, RowValue in enumerate(Quads) if Index != Spoke),
        *FlexRows(Layout),
    ]


def PinRows(Layout: CapLayout, Spoke: int) -> list[KCapRow]:
    Reach = range(2, KPinReach + 1)
    Pinned: list[KCapKey] = [
        ("spoke", Spoke, Index) for Index in range(1, KPinReach + 1)
    ]
    Pinned += [SectorKey(Layout, Spoke, Index, 1) for Index in Reach]
    Pinned += [SectorKey(Layout, Spoke - 1, 1, Index) for Index in Reach]
    Found: list[KCapRow] = []
    for CapKey in Pinned:
        Dense = EmptyRow(Layout)
        Dense[Layout.Slots[CapKey]] = 1.0
        Found.append(DeltaRow(Layout, Dense, {}))
    return Found


def KeptWindows(
    Layout: CapLayout,
    Ratios: tuple[tuple[Fraction, ...], tuple[Fraction, ...]],
    Spoke: int,
) -> tuple[list[KCapRow], list[float]]:
    Valence = Layout.Valence
    Count = len(KWindowRows)
    Windows = WindowRows(Layout, *Ratios)
    Upper = (Spoke + 1) % Valence * Count + KOddWindow
    Lower = (Spoke - 1) % Valence * Count + KOddWindow
    Dropped = {Spoke * Count + KEvenWindow, Upper, Lower}
    Found = [RowValue for Index, RowValue in enumerate(Windows) if Index not in Dropped]
    Summed = [
        LeftValue + RightValue
        for LeftValue, RightValue in zip(Windows[Upper][0], Windows[Lower][0])
    ]
    Found.append(DeltaRow(Layout, Summed, {}))
    return Found, Windows[Upper][0]


def CreaseRing(
    Layout: CapLayout, Limit: KPoleRow, RatiosI: tuple[Fraction, ...], Spoke: int
) -> list[KCapRow]:
    SlotIndex = Layout.Slots[("spoke", Spoke, 1)]
    Virtual = MixRows(
        (
            (0.5, NetRow(Layout, SectorKey(Layout, Spoke, 1, 1))),
            (0.5, NetRow(Layout, SectorKey(Layout, Spoke - 1, 1, 1))),
        )
    )
    Netref = list(Layout.Netref)
    Netref[SlotIndex] = Virtual
    Shifted = ReplaceFields(Layout, Netref=tuple(Netref))
    Found: list[KCapRow] = []
    for Dense, SideRow in RingRows(Shifted, Limit, RatiosI):
        Weight = Dense[SlotIndex]
        Parts = ((1.0, SideRow), (Weight, Layout.Netref[SlotIndex]), (-Weight, Virtual))
        Found.append((Dense, MixRows(Parts)))
    return Found


def CreaseTangent(
    Layout: CapLayout, RatiosI: tuple[Fraction, ...], Spoke: int
) -> KCapRow:
    CosineRow, SineRow = TangentRows(Layout, RatiosI)
    Angle = 2.0 * math.pi * Spoke / Layout.Valence
    return CombineRows(((RoundCosine(Angle), SineRow), (-RoundSine(Angle), CosineRow)))


def WedgeRow(Layout: CapLayout, Spoke: int) -> KCapRow:
    Valence = Layout.Valence
    Cosine = RoundCosine(2.0 * math.pi / Valence)
    Dense = EmptyRow(Layout)
    for TermKind, IndexI, IndexJ, Steady, Tilted in KWedgeTerms:
        KeyPair: list[KCapKey] = [
            ("spoke", (Spoke + 1) % Valence, IndexJ),
            ("spoke", (Spoke - 1) % Valence, IndexJ),
        ]
        if TermKind == "A":
            KeyPair = [
                SectorKey(Layout, Spoke, IndexI, IndexJ),
                SectorKey(Layout, Spoke - 1, IndexJ, IndexI),
            ]
        for CapKey in dict.fromkeys(KeyPair):
            Dense[Layout.Slots[CapKey]] += float(Steady) + float(Tilted) * Cosine
    return DeltaRow(Layout, Dense, {})


def SectorTotal(
    Layout: CapLayout, Limit: KPoleRow, Places: tuple[tuple[int, int], ...]
) -> KPoleRow:
    Valence = Layout.Valence
    Share = 1.0 / len(Places)
    Parts: list[tuple[float, KPoleRow]] = [(-float(Valence), Limit)]
    for Sector in range(Valence):
        Parts += [
            (Share, NetRow(Layout, SectorKey(Layout, Sector, *Place)))
            for Place in Places
        ]
    return MixRows(Parts)


def CreaseDefect(Layout: CapLayout, Spoke: int, Index: int) -> KPoleRow:
    return MixRows(
        (
            (0.5, NetRow(Layout, SectorKey(Layout, Spoke, Index, 1))),
            (0.5, NetRow(Layout, SectorKey(Layout, Spoke - 1, 1, Index))),
            (-1.0, NetRow(Layout, ("spoke", Spoke, Index))),
        )
    )


def OddSide(Layout: CapLayout, Limit: KPoleRow, Spoke: int) -> KPoleRow:
    Valence = Layout.Valence
    First = CreaseDefect(Layout, Spoke, 1)
    Second = CreaseDefect(Layout, Spoke, 2)
    if Valence == 3:
        Twist = SectorTotal(Layout, Limit, ((1, 1),))
        Weights = [float(Value) for Value in KTripleOdd]
        return MixRows(zip(Weights, (Twist, First, Second)))
    Cosine = RoundCosine(2.0 * math.pi / Valence)
    Scale = 16.0 * Cosine / (Valence * (Valence - 3))
    Blend = float(Fraction(5 * Valence + 7, 2 * (4 * Valence - 7)))
    Mixed = SectorTotal(Layout, Limit, ((1, 2), (2, 1)))
    Square = SectorTotal(Layout, Limit, ((2, 2),))
    Parts = (
        (Scale, First),
        (-2.0 * Scale, Second),
        (Scale * (1.0 + Blend), Square),
        (-4.0 * Scale * Blend, Mixed),
    )
    return MixRows(Parts)


def CreaseRows(
    Layout: CapLayout,
    Limit: KPoleRow,
    Ratios: tuple[tuple[Fraction, ...], tuple[Fraction, ...]],
    Creased: tuple[bool, ...],
) -> list[KCapRow]:
    return CreaseBody(Layout, Limit, Ratios, CreaseSpoke(Creased))


def CreaseBody(
    Layout: CapLayout,
    Limit: KPoleRow,
    Ratios: tuple[tuple[Fraction, ...], tuple[Fraction, ...]],
    Spoke: int,
) -> list[KCapRow]:
    if any(Ratio != KCreaseRatio for Ratio in Ratios[0] + Ratios[1]):
        raise ValueError(
            "Fusion Form crease cap rule was measured at knot ratio 2/3 only"
        )
    Windows, OddDense = KeptWindows(Layout, Ratios, Spoke)
    return [
        *KeptHard(Layout, Limit, Spoke),
        *PinRows(Layout, Spoke),
        *Windows,
        DeltaRow(Layout, OddDense, OddSide(Layout, Limit, Spoke)),
        *CreaseRing(Layout, Limit, Ratios[0], Spoke),
        CreaseTangent(Layout, Ratios[0], Spoke),
        *TwistRows(Layout),
        WedgeRow(Layout, Spoke),
    ]
