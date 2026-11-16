from dataclasses import dataclass as MakeDataClass
from fractions import Fraction
from typing import Callable as KCallable, Mapping as KMapping

from convert.Formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import KPoleRow

# the cap key shape must stay shared so spline pole reconstruction uses one contract for compatible values
KCapKey = tuple[str | int, ...]

# the place key shape must stay shared so spline pole reconstruction uses one contract for compatible values
KPlaceKey = tuple[int, int, int]

# the sector knots shape must stay shared so spline pole reconstruction uses one contract for compatible values
KSectorKnots = tuple[tuple[Fraction, int], ...]


# cap sector needs an explicit state contract so neighboring patches retain consistent subdivision boundaries
@MakeDataClass(frozen=True, slots=True)
class CapSector:
    FaceIndex: int
    KnotsI: KSectorKnots
    KnotsJ: KSectorKnots


# cap input needs an explicit state contract so neighboring patches retain consistent subdivision boundaries
@MakeDataClass(frozen=True, slots=True)
class CapInput:
    Vertex: int
    Valence: int
    Level: int
    Creased: tuple[bool, ...]
    Sectors: tuple[CapSector, ...]
    Limit: KPoleRow | None
    Reference: KMapping[KCapKey, KPoleRow]
    Places: KMapping[KCapKey, tuple[KPlaceKey, ...]]
    Unknown: frozenset[KCapKey]


# cap hook must remain consistent across callers so neighboring patches retain consistent subdivision boundaries
KCapHook = KCallable[[CapInput], KMapping[KCapKey, KPoleRow]]


# the spoke key contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def SpokeKey(Sector: int, Valence: int, IndexI: int, IndexJ: int) -> KCapKey:
    if IndexI == 0 and IndexJ == 0:
        return ("ep",)
    if IndexJ == 0:
        return ("spoke", Sector, IndexI)
    if IndexI == 0:
        return ("spoke", (Sector + 1) % Valence, IndexJ)
    return ("in", Sector, IndexI, IndexJ)
