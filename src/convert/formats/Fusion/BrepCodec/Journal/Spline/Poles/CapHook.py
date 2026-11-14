from dataclasses import dataclass as MakeDataClass
from fractions import Fraction
from typing import Callable as KCallable, Mapping as KMapping

from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import KPoleRow

KCapKey = tuple[str | int, ...]
KPlaceKey = tuple[int, int, int]
KSectorKnots = tuple[tuple[Fraction, int], ...]


@MakeDataClass(frozen=True, slots=True)
class CapSector:
    FaceIndex: int
    KnotsI: KSectorKnots
    KnotsJ: KSectorKnots


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


KCapHook = KCallable[[CapInput], KMapping[KCapKey, KPoleRow]]


def SpokeKey(Sector: int, Valence: int, IndexI: int, IndexJ: int) -> KCapKey:
    if IndexI == 0 and IndexJ == 0:
        return ("ep",)
    if IndexJ == 0:
        return ("spoke", Sector, IndexI)
    if IndexI == 0:
        return ("spoke", (Sector + 1) % Valence, IndexJ)
    return ("in", Sector, IndexI, IndexJ)
