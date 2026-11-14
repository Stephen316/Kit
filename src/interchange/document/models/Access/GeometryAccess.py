from __future__ import annotations

from typing import Mapping as TypeMap
from typing import Protocol, cast as CastValue

from interchange.brep.topology.BrepModel import BrepModel
from interchange.enums.EnumUnits import UnitSystem


class GeometryFields(Protocol):
    metadata: TypeMap[str, object]
    units: UnitSystem
    schema_version: str
    brep: BrepModel | None


class GeometryAccess:
    locals()["__slots__"] = ()

    @property
    def Metadata(self) -> TypeMap[str, object]:
        return CastValue(GeometryFields, self).metadata

    @property
    def Units(self) -> UnitSystem:
        return CastValue(GeometryFields, self).units

    @property
    def SchemaVersion(self) -> str:
        return CastValue(GeometryFields, self).schema_version

    @property
    def BrepModel(self) -> BrepModel | None:
        return CastValue(GeometryFields, self).brep
