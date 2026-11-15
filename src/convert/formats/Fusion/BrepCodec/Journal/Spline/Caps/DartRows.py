from fractions import Fraction

from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.CapLayout import (
    KReach,
    KCapRow,
    CapLayout,
    DeltaRow,
    EmptyRow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.CreaseRows import (
    KDartValence,
    CreaseBody,
    CreaseDefect,
    SectorKey,
    SectorTotal,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import KCapKey
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KPoleRow,
    MixRows,
)

# the dart term shape must stay shared so spline cap reconstruction uses one contract for compatible values
KDartTerm = tuple[int, int, int, int]

# the dart row shape must stay shared so spline cap reconstruction uses one contract for compatible values
KDartRow = tuple[int, tuple[KDartTerm, ...], tuple[int, int, int, int]]

# the dart rows order must stay explicit so extraordinary vertices remain compatible with surrounding patches
KDartRows: tuple[KDartRow, ...] = (
    (
        1,
        (
            (0, 1, 2, 1),
            (0, 1, 3, -1),
            (0, 1, 4, 1),
            (1, 2, 1, 1),
            (1, 3, 1, -1),
        ),
        (0, 0, 0, 0),
    ),
    (
        1,
        (
            (2, 2, 0, -1),
            (2, 3, 0, 1),
            (2, 4, 0, 1),
            (0, 3, 3, -1),
            (0, 3, 4, -1),
            (0, 4, 3, -2),
            (1, 1, 4, 1),
            (1, 3, 2, 1),
        ),
        (0, 0, 0, 0),
    ),
    (
        1,
        (
            (1, 4, 0, 1),
            (2, 3, 0, -1),
            (2, 4, 0, -1),
            (0, 1, 2, -1),
            (0, 1, 3, 1),
            (0, 2, 2, 1),
            (0, 2, 3, -1),
            (0, 2, 4, 1),
            (0, 3, 2, -1),
            (0, 3, 3, -1),
            (0, 3, 4, 1),
            (1, 2, 4, 2),
            (1, 3, 4, 1),
            (1, 4, 2, -1),
        ),
        (0, 0, 0, 0),
    ),
    (
        1,
        (
            (1, 3, 0, -1),
            (2, 2, 0, 1),
            (0, 2, 2, 2),
            (0, 2, 3, 6),
            (0, 2, 4, 3),
            (0, 3, 2, -2),
            (0, 3, 3, 1),
            (0, 3, 4, -1),
            (1, 1, 3, 1),
            (1, 1, 4, -1),
            (1, 2, 2, -2),
            (1, 2, 3, -2),
            (1, 3, 1, -1),
            (1, 3, 2, -1),
        ),
        (1, -1, 0, 0),
    ),
    (
        1,
        (
            (1, 3, 0, -1),
            (1, 4, 0, 1),
            (2, 1, 0, -1),
            (0, 1, 2, -1),
            (0, 2, 2, 8),
            (0, 2, 3, 2),
            (0, 2, 4, 1),
            (0, 3, 2, 6),
            (0, 3, 4, 1),
            (0, 4, 2, 3),
            (0, 4, 3, 1),
            (1, 1, 1, -1),
            (1, 1, 3, 1),
            (1, 2, 1, -1),
            (1, 2, 2, -2),
            (1, 2, 4, -1),
            (1, 3, 1, -1),
            (1, 3, 4, 1),
            (1, 4, 2, -1),
        ),
        (0, -1, 2, -1),
    ),
    (
        -1,
        (
            (0, 2, 2, -1),
            (1, 2, 2, 1),
        ),
        (0, 0, 0, 0),
    ),
    (
        -1,
        (
            (0, 4, 2, -1),
            (1, 2, 4, 1),
        ),
        (0, 0, 0, 0),
    ),
    (
        -1,
        (
            (0, 2, 4, 1),
            (1, 3, 2, -1),
            (1, 3, 3, 1),
        ),
        (0, 0, 0, 0),
    ),
    (
        -1,
        (
            (0, 2, 2, -1),
            (0, 3, 2, 2),
            (1, 2, 3, 1),
        ),
        (0, 0, 0, 0),
    ),
    (
        -1,
        (
            (1, 4, 0, 1),
            (0, 1, 1, -1),
            (0, 3, 3, -1),
            (0, 4, 3, 1),
            (1, 1, 1, -1),
            (1, 2, 2, -1),
            (1, 3, 2, 1),
        ),
        (0, 0, 0, 0),
    ),
)


# the dart decision must stay consistent so extraordinary vertices remain compatible with surrounding patches
def IsDart(Creased: tuple[bool, ...]) -> bool:
    return len(Creased) == KDartValence and sum(Creased) == 1


# dart spoke needs an explicit validity boundary so extraordinary vertices remain compatible with surrounding patches
def DartSpoke(Creased: tuple[bool, ...]) -> int:
    if not IsDart(Creased):
        raise ValueError(
            "Fusion Form dart rule covers one creased spoke at a valence 4 vertex"
        )
    return Creased.index(True)


# the dart hidden contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def DartHidden(Spoke: int) -> frozenset[KCapKey]:
    Found: set[KCapKey] = {("ep",)}
    for Offset in (1, -1):
        Found |= {
            ("spoke", (Spoke + Offset) % KDartValence, Index)
            for Index in range(1, KReach + 1)
        }
    return frozenset(Found)


# the relative key contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def RelativeKey(Spoke: int, Offset: int, IndexI: int, IndexJ: int) -> KCapKey:
    Sector = (Spoke + Offset) % KDartValence
    if IndexJ == 0:
        return ("spoke", Sector, IndexI)
    return ("in", Sector, IndexI, IndexJ)


# the mirror term contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def MirrorTerm(Offset: int, IndexI: int, IndexJ: int) -> tuple[int, int, int]:
    if IndexJ == 0:
        return -Offset, IndexI, 0
    return -1 - Offset, IndexJ, IndexI


# the orbit row contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def OrbitRow(
    Layout: CapLayout, Spoke: int, Parity: int, Terms: tuple[KDartTerm, ...]
) -> list[float]:
    Dense = EmptyRow(Layout)
    for Offset, IndexI, IndexJ, Weight in Terms:
        First = RelativeKey(Spoke, Offset, IndexI, IndexJ)
        Second = RelativeKey(Spoke, *MirrorTerm(Offset, IndexI, IndexJ))
        Dense[Layout.Slots[First]] += Weight
        if Second != First:
            Dense[Layout.Slots[Second]] += Parity * Weight
    return Dense


# the dart side contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def DartSide(
    Layout: CapLayout, Limit: KPoleRow, Spoke: int, Weights: tuple[int, ...]
) -> KPoleRow:
    Features = (
        CreaseDefect(Layout, Spoke, 1),
        CreaseDefect(Layout, Spoke, 2),
        SectorTotal(Layout, Limit, ((1, 2), (2, 1))),
        SectorTotal(Layout, Limit, ((2, 2),)),
    )
    return MixRows(
        (float(Weight), Feature) for Weight, Feature in zip(Weights, Features)
    )


# the middle rows contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def MiddleRows(Layout: CapLayout, Spoke: int) -> list[KCapRow]:
    Triples: list[tuple[KCapKey, KCapKey, KCapKey]] = [
        (
            ("spoke", Upper % KDartValence, Index),
            SectorKey(Layout, Upper, Index, 1),
            SectorKey(Layout, Upper - 1, 1, Index),
        )
        for Upper in (Spoke + 1, Spoke - 1)
        for Index in range(1, KReach + 1)
    ]
    Opposite = (Spoke + KDartValence // 2) % KDartValence
    Triples.append((("ep",), ("spoke", Spoke, 1), ("spoke", Opposite, 1)))
    Found: list[KCapRow] = []
    for Middle, Lower, Higher in Triples:
        Dense = EmptyRow(Layout)
        Dense[Layout.Slots[Middle]] += 1.0
        Dense[Layout.Slots[Lower]] -= 0.5
        Dense[Layout.Slots[Higher]] -= 0.5
        Found.append((Dense, {}))
    return Found


# the dart rows contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def DartRows(
    Layout: CapLayout,
    Limit: KPoleRow,
    Ratios: tuple[tuple[Fraction, ...], tuple[Fraction, ...]],
    Spoke: int,
) -> list[KCapRow]:
    Found = [*CreaseBody(Layout, Limit, Ratios, Spoke), *MiddleRows(Layout, Spoke)]
    for Parity, Terms, Weights in KDartRows:
        Dense = OrbitRow(Layout, Spoke, Parity, Terms)
        Found.append(DeltaRow(Layout, Dense, DartSide(Layout, Limit, Spoke, Weights)))
    return Found
