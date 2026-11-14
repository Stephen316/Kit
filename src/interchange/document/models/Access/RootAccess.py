from __future__ import annotations

from typing import Protocol, cast as CastValue

from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordParameter import Parameter
from interchange.records.RecordSource import CadSource


class RootFields(Protocol):
    source: CadSource
    configurations: tuple[Configuration, ...]
    parameters: tuple[Parameter, ...]
    support_planes: tuple[SupportPlane, ...]
    sketches: tuple[Sketch, ...]
    selections: tuple[Selection, ...]


class RootAccess:
    locals()["__slots__"] = ()

    @property
    def Source(self) -> CadSource:
        return CastValue(RootFields, self).source

    @property
    def Configurations(self) -> tuple[Configuration, ...]:
        return CastValue(RootFields, self).configurations

    @property
    def Parameters(self) -> tuple[Parameter, ...]:
        return CastValue(RootFields, self).parameters

    @property
    def SupportPlanes(self) -> tuple[SupportPlane, ...]:
        return CastValue(RootFields, self).support_planes

    @property
    def Sketches(self) -> tuple[Sketch, ...]:
        return CastValue(RootFields, self).sketches

    @property
    def Selections(self) -> tuple[Selection, ...]:
        return CastValue(RootFields, self).selections
