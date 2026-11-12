from dataclasses import dataclass as Dataclass
from typing import Mapping as TypeMap

from interchange.geometry.models.Selection import SelectPathElem


# a qualified pick carries its native source chain and any neutral path it resolves
@Dataclass(frozen=True, slots=True)
class RevolvePick:
    ObjectId: int | None
    Descriptor: int
    Terminal: int
    PathElems: tuple[SelectPathElem, ...] = ()
    DependencyId: str | None = None
    RelatedIds: tuple[int, ...] = ()
    EdgeSource: TypeMap[str, object] | None = None
