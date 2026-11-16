from __future__ import annotations

from typing import Protocol, cast as CastValue

from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter
from interchange.Records.RecordSource import CadSource


# root fields needs an explicit state contract so independent adapters agree on document semantics
class RootFields(Protocol):
    source: CadSource
    configurations: tuple[Configuration, ...]
    parameters: tuple[Parameter, ...]
    support_planes: tuple[SupportPlane, ...]
    sketches: tuple[Sketch, ...]
    selections: tuple[Selection, ...]


# the root access contract needs a dedicated boundary so independent adapters agree on document semantics
class RootAccess:
    locals()["__slots__"] = ()

    # the source contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def Source(self) -> CadSource:
        return CastValue(RootFields, self).source

    # the configurations contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def Configurations(self) -> tuple[Configuration, ...]:
        return CastValue(RootFields, self).configurations

    # the parameters contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def Parameters(self) -> tuple[Parameter, ...]:
        return CastValue(RootFields, self).parameters

    # the support planes contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def SupportPlanes(self) -> tuple[SupportPlane, ...]:
        return CastValue(RootFields, self).support_planes

    # the sketches contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def Sketches(self) -> tuple[Sketch, ...]:
        return CastValue(RootFields, self).sketches

    # selections must resolve unambiguously so independent adapters agree on document semantics
    @property
    def Selections(self) -> tuple[Selection, ...]:
        return CastValue(RootFields, self).selections
