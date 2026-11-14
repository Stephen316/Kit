import math
from fractions import Fraction

from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.CapLayout import (
    KCapRow,
    CapLayout,
    DeltaRow,
    EmptyRow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KPoleRow,
    MixRows,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.RoundTrig import (
    RoundCosine,
    RoundSine,
)

KWeightTriple = tuple[Fraction, Fraction, Fraction]
KRingWeights: dict[Fraction, KWeightTriple] = {
    Fraction(2, 3): (Fraction(37, 104), Fraction(83, 52), Fraction(43, 26)),
    Fraction(1, 2): (Fraction(9, 40), Fraction(21, 20), Fraction(6, 5)),
}
KTangentWeights: dict[Fraction, KWeightTriple] = {
    Fraction(2, 3): (Fraction(-17, 468), Fraction(4, 117), Fraction(-49, 468)),
    Fraction(1, 2): (Fraction(0), Fraction(-1, 24), Fraction(-1, 24)),
}


def RatioWeights(
    Table: dict[Fraction, KWeightTriple], Ratio: Fraction
) -> tuple[float, float, float]:
    Found = Table.get(Ratio)
    if Found is None:
        raise ValueError(
            "Fusion Form cap rule has no ring weights for knot ratio " + str(Ratio)
        )
    return float(Found[0]), float(Found[1]), float(Found[2])


def SpokeSlot(Layout: CapLayout, Spoke: int, Index: int) -> int:
    return Layout.Slots[("spoke", Spoke % Layout.Valence, Index)]


def SectorLine(
    Layout: CapLayout, Sector: int, Ratios: tuple[Fraction, ...]
) -> list[float]:
    Valence = Layout.Valence
    Cosine = RoundCosine(2.0 * math.pi / Valence)
    Dense = EmptyRow(Layout)
    Dense[Layout.Slots[("in", Sector % Valence, 1, 1)]] += Cosine
    for Spoke in (Sector, Sector + 1):
        _, Second, Third = RatioWeights(KRingWeights, Ratios[Spoke % Valence])
        Dense[SpokeSlot(Layout, Spoke, 2)] -= Second
        Dense[SpokeSlot(Layout, Spoke, 3)] += Third
    return Dense


def NetTangents(Layout: CapLayout, Limit: KPoleRow) -> list[KPoleRow]:
    return [
        MixRows(((1.0, Layout.Netref[SpokeSlot(Layout, Spoke, 1)]), (-1.0, Limit)))
        for Spoke in range(Layout.Valence)
    ]


def RingRows(
    Layout: CapLayout, Limit: KPoleRow, Ratios: tuple[Fraction, ...]
) -> list[KCapRow]:
    Valence = Layout.Valence
    Cosine = RoundCosine(2.0 * math.pi / Valence)
    Kappa = (Valence - 4) * Cosine / (Valence + 5)
    Spread = 9.0 * Cosine / (Valence + 5)
    Tangents = NetTangents(Layout, Limit)
    Average = MixRows((1.0 / Valence, Tangent) for Tangent in Tangents)
    Found: list[KCapRow] = []
    for Spoke in range(Valence):
        Prior = SectorLine(Layout, Spoke - 1, Ratios)
        Later = SectorLine(Layout, Spoke, Ratios)
        Dense = [
            0.5 * (LeftValue + RightValue)
            for LeftValue, RightValue in zip(Prior, Later)
        ]
        for Other, Scalar in ((Spoke - 1, 1.0), (Spoke, 2.0), (Spoke + 1, 1.0)):
            First, _, _ = RatioWeights(KRingWeights, Ratios[Other % Valence])
            Dense[SpokeSlot(Layout, Other, 1)] += Scalar * First
        SideRow = MixRows(((-Kappa, Tangents[Spoke]), (-Spread, Average)))
        Found.append(DeltaRow(Layout, Dense, SideRow))
    return Found


def TangentRows(Layout: CapLayout, Ratios: tuple[Fraction, ...]) -> list[KCapRow]:
    Valence = Layout.Valence
    Cosine = RoundCosine(2.0 * math.pi / Valence)
    Found: list[KCapRow] = []
    for Phase in (RoundCosine, RoundSine):
        Dense = EmptyRow(Layout)
        for Spoke in range(Valence):
            First, Second, Third = RatioWeights(KRingWeights, Ratios[Spoke])
            Tilts = RatioWeights(KTangentWeights, Ratios[Spoke])
            Terms = (
                2.0 * First + Cosine * Tilts[0],
                -Second + Cosine * Tilts[1],
                Third + Cosine * Tilts[2],
            )
            Angle = Phase(2.0 * math.pi * Spoke / Valence)
            for Index, Value in enumerate(Terms, start=1):
                Dense[SpokeSlot(Layout, Spoke, Index)] += Angle * Value
        Found.append(DeltaRow(Layout, Dense, {}))
    return Found


def TwistRows(Layout: CapLayout) -> list[KCapRow]:
    Valence = Layout.Valence
    if Valence % 2:
        return []
    Dense = EmptyRow(Layout)
    for Sector in range(Valence):
        Dense[Layout.Slots[("in", Sector, 1, 1)]] = float((-1) ** Sector)
    Shrink = -(Valence - 4) / (Valence + 5)
    SideRow = MixRows(
        (Shrink * Value, Layout.Netref[SlotIndex])
        for SlotIndex, Value in enumerate(Dense)
        if Value
    )
    return [DeltaRow(Layout, Dense, SideRow)]
