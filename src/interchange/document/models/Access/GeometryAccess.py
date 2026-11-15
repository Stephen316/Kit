from __future__ import annotations

from typing import Mapping as TypeMap
from typing import Protocol, cast as CastValue

from interchange.brep.topology.BrepModel import BrepModel
from interchange.enums.EnumUnits import UnitSystem


# geometry fields needs an explicit state contract so independent adapters agree on document semantics
class GeometryFields(Protocol):
    metadata: TypeMap[str, object]
    units: UnitSystem
    schema_version: str
    brep: BrepModel | None


# the geometry access contract needs a dedicated boundary so independent adapters agree on document semantics
class GeometryAccess:
    locals()["__slots__"] = ()

    # the metadata contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def Metadata(self) -> TypeMap[str, object]:
        return CastValue(GeometryFields, self).metadata

    # units needs one geometric convention so independent adapters agree on document semantics
    @property
    def Units(self) -> UnitSystem:
        return CastValue(GeometryFields, self).units

    # the schema version contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def SchemaVersion(self) -> str:
        return CastValue(GeometryFields, self).schema_version

    # the boundary representation model contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def BrepModel(self) -> BrepModel | None:
        return CastValue(GeometryFields, self).brep
