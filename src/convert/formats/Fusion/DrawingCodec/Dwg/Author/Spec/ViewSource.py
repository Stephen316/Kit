from dataclasses import dataclass as MakeDataClass

from interchange.brep.topology.BrepModel import BrepModel

KPointTriple = tuple[float, float, float]


@MakeDataClass(frozen=True, slots=True)
class ViewSource:
    BodyId: int
    ComponentText: str
    GeometryGuid: str
    BoundsMin: KPointTriple
    BoundsMax: KPointTriple
    MaterialText: str = ""
    OccurrencePath: tuple[int, ...] = ()
    Solid: BrepModel | None = None
