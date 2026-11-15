from dataclasses import dataclass as MakeDataClass

from interchange.brep.topology.BrepModel import BrepModel

# the point triple shape must stay shared so native drawing authoring uses one contract for compatible values
KPointTriple = tuple[float, float, float]


# view source needs an explicit state contract so drawing objects retain valid ownership and reference relationships
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
