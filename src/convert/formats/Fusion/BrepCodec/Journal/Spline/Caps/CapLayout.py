from dataclasses import dataclass as MakeDataClass
from fractions import Fraction
from typing import Iterable as KIterable, Mapping as KMapping

from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.CapKnots import (
    KKnotTuple,
    BasisDerive,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import (
    KCapKey,
    SpokeKey,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KPoleRow,
    MixRows,
)

# reach must remain consistent across callers so extraordinary vertices remain compatible with surrounding patches
KReach = 4

# span must remain consistent across callers so extraordinary vertices remain compatible with surrounding patches
KSpan = 8

# the cap row shape must stay shared so spline cap reconstruction uses one contract for compatible values
KCapRow = tuple[list[float], KPoleRow]


# cap layout needs an explicit state contract so extraordinary vertices remain compatible with surrounding patches
@MakeDataClass(frozen=True, slots=True)
class CapLayout:
    Valence: int
    KnotsI: tuple[KKnotTuple, ...]
    KnotsJ: tuple[KKnotTuple, ...]
    Slots: KMapping[KCapKey, int]
    Reference: KMapping[KCapKey, KPoleRow]
    Netref: tuple[KPoleRow, ...]


# the cap keys contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def CapKeys(Valence: int) -> tuple[KCapKey, ...]:
    Found: list[KCapKey] = [("ep",)]
    Found += [
        ("spoke", Sector, Index)
        for Sector in range(Valence)
        for Index in range(1, KReach + 1)
    ]
    Found += [
        ("in", Sector, IndexI, IndexJ)
        for Sector in range(Valence)
        for IndexI in range(1, KReach + 1)
        for IndexJ in range(1, KReach + 1)
        if (IndexI, IndexJ) != (KReach, KReach)
    ]
    return tuple(Found)


# the empty row contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def EmptyRow(Layout: CapLayout) -> list[float]:
    return [0.0] * len(Layout.Slots)


# the term operation needs a consistent construction rule so extraordinary vertices remain compatible with surrounding patches
def AddTermMut(
    Layout: CapLayout,
    Target: tuple[list[float], list[tuple[float, KPoleRow]]],
    CapKey: KCapKey,
    Scalar: float,
) -> None:
    Dense, Moved = Target
    SlotIndex = Layout.Slots.get(CapKey)
    if SlotIndex is not None:
        Dense[SlotIndex] += Scalar
        return
    RowValue = Layout.Reference.get(CapKey)
    if RowValue is None:
        raise ValueError("Fusion Form cap rule has no reference pole " + str(CapKey))
    Moved.append((-Scalar, RowValue))


# the surface row contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def SurfaceRow(
    Layout: CapLayout,
    Sector: int,
    Params: tuple[Fraction, Fraction],
    Orders: tuple[int, int],
) -> KCapRow:
    Valence = Layout.Valence
    Wrapped = Sector % Valence
    BasisI = BasisDerive(Layout.KnotsI[Wrapped], Params[0], Orders[0], False)
    BasisJ = BasisDerive(Layout.KnotsJ[Wrapped], Params[1], Orders[1], False)
    Dense = EmptyRow(Layout)
    Moved: list[tuple[float, KPoleRow]] = []
    for IndexI, ValueI in enumerate(BasisI[:KSpan]):
        for IndexJ, ValueJ in enumerate(BasisJ[:KSpan]):
            Scalar = ValueI * ValueJ
            if Scalar:
                AddTermMut(
                    Layout,
                    (Dense, Moved),
                    SpokeKey(Wrapped, Valence, IndexI, IndexJ),
                    float(Scalar),
                )
    return Dense, MixRows(Moved)


# the combine rows contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def CombineRows(Parts: KIterable[tuple[float, KCapRow]]) -> KCapRow:
    Dense: list[float] = []
    Sides: list[tuple[float, KPoleRow]] = []
    for Scalar, (Coefficients, SideRow) in Parts:
        if not Dense:
            Dense = [0.0] * len(Coefficients)
        for SlotIndex, Value in enumerate(Coefficients):
            if Value:
                Dense[SlotIndex] += Scalar * Value
        Sides.append((Scalar, SideRow))
    return Dense, MixRows(Sides)


# the delta row contract needs a shared interpretation so extraordinary vertices remain compatible with surrounding patches
def DeltaRow(Layout: CapLayout, Dense: list[float], SideRow: KPoleRow) -> KCapRow:
    Parts = [(1.0, SideRow)]
    Parts += [
        (Value, Layout.Netref[SlotIndex])
        for SlotIndex, Value in enumerate(Dense)
        if Value
    ]
    return Dense, MixRows(Parts)
