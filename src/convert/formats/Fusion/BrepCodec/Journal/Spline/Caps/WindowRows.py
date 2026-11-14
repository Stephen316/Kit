import math
from fractions import Fraction

from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.CapLayout import (
    KCapRow,
    CapLayout,
    DeltaRow,
    EmptyRow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import KCapKey
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.RoundTrig import RoundCosine

KWindowTerm = tuple[str, int, int, int, int]
KWindowRows: tuple[tuple[KWindowTerm, ...], ...] = (
    (
        ("B12", 1, 0, 0, 0),
        ("A21", -1, 0, 0, 0),
    ),
    (
        ("B13", 1, 0, 0, 0),
        ("A31", -1, 0, 0, 0),
    ),
    (
        ("B14", 1, 0, 0, 0),
        ("A41", -1, 0, 0, 0),
    ),
    (
        ("A41", 1, 0, 0, 0),
        ("A14", 1, 0, 0, 0),
        ("A21", -2, 0, 0, 0),
        ("A12", -2, 0, 0, 0),
        ("A31", 2, 0, 0, 0),
        ("A13", 2, 0, 0, 0),
        ("A22", 8, 0, 0, 0),
        ("A23", -8, 0, 0, 0),
        ("A32", -8, 0, 0, 0),
        ("A33", 8, 0, 0, 0),
    ),
    (
        ("S0.1", -8, 0, 0, 0),
        ("S0.2", 16, 0, 0, 0),
        ("S0.3", -12, 0, 0, 0),
        ("S0.4", 4, 0, 1, 0),
        ("S+1.1", -8, 0, 0, 0),
        ("S+1.2", 16, 0, 0, 0),
        ("S+1.3", -12, 0, 0, 0),
        ("S+1.4", 4, 0, 1, 0),
        ("A13", -8, 0, 0, 0),
        ("A31", -8, 0, 0, 0),
        ("A33", 32, 0, 0, 0),
    ),
    (
        ("S0.1", -36, 28, 0, 0),
        ("S0.2", 66, -54, 0, 0),
        ("S0.3", -78, 70, 0, 0),
        ("B11", 18, -18, 0, 0),
        ("A11", 18, -18, 0, 0),
        ("B12", -33, 27, 0, 0),
        ("A21", -33, 27, 0, 0),
        ("B21", 0, 8, 0, 0),
        ("A12", 0, 8, 0, 0),
        ("B13", 39, -19, 0, 0),
        ("A31", 39, -19, 0, 0),
        ("B31", 0, -8, 0, 0),
        ("A13", 0, -8, 0, 0),
        ("B23", 0, -32, 0, 0),
        ("A32", 0, -32, 0, 0),
        ("B33", 0, 32, 0, 0),
        ("A33", 0, 32, 0, 0),
    ),
    (
        ("S-1.1", 9, -28, 0, 0),
        ("S+1.1", -9, 28, 0, 0),
        ("S-1.2", -12, 56, 0, 0),
        ("S+1.2", 12, -56, 0, 0),
        ("S-1.4", -24, 24, 3, 0),
        ("S+1.4", 24, -24, -3, 0),
        ("B22", -24, -64, 0, 0),
        ("A22", 24, 64, 0, 0),
        ("B23", 24, 128, 0, 0),
        ("A32", -24, -128, 0, 0),
        ("B32", 24, -192, 0, 0),
        ("A23", -24, 192, 0, 0),
        ("B33", 72, 384, 0, 0),
        ("A33", -72, -384, 0, 0),
    ),
)


def WindowKey(LocalName: str, Spoke: int, Valence: int) -> KCapKey:
    if LocalName[0] == "S":
        Offset, Index = LocalName[1:].split(".")
        return ("spoke", (Spoke + int(Offset)) % Valence, int(Index))
    Sector = Spoke if LocalName[0] == "A" else Spoke - 1
    return ("in", Sector % Valence, int(LocalName[1]), int(LocalName[2]))


def KeyRatio(
    CapKey: KCapKey, RatiosI: tuple[Fraction, ...], RatiosJ: tuple[Fraction, ...]
) -> Fraction:
    Sector = int(CapKey[1])
    if CapKey[0] == "spoke":
        return RatiosI[Sector] if CapKey[2] == 4 else Fraction(0)
    if CapKey[2] == 4:
        return RatiosI[Sector]
    if CapKey[3] == 4:
        return RatiosJ[Sector]
    return Fraction(0)


def WindowRows(
    Layout: CapLayout, RatiosI: tuple[Fraction, ...], RatiosJ: tuple[Fraction, ...]
) -> list[KCapRow]:
    Valence = Layout.Valence
    Cosine = RoundCosine(2.0 * math.pi / Valence)
    Found: list[KCapRow] = []
    for Spoke in range(Valence):
        for Terms in KWindowRows:
            Dense = EmptyRow(Layout)
            for LocalName, Steady, Tilted, RatioSteady, RatioTilted in Terms:
                CapKey = WindowKey(LocalName, Spoke, Valence)
                Ratio = float(KeyRatio(CapKey, RatiosI, RatiosJ))
                Dense[Layout.Slots[CapKey]] += (
                    Steady
                    + Tilted * Cosine
                    + Ratio * (RatioSteady + RatioTilted * Cosine)
                )
            Found.append(DeltaRow(Layout, Dense, {}))
    return Found
