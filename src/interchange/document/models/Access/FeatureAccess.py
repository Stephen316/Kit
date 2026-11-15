from __future__ import annotations

from typing import Protocol, cast as CastValue

from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.mesh.SurfaceMesh import SurfaceMesh
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.records.RecordDiagnostic import Diagnostic


# feature fields needs an explicit state contract so independent adapters agree on document semantics
class FeatureFields(Protocol):
    feature_timeline: tuple[FeatureStep, ...]
    bodies: tuple[DesignBody, ...]
    meshes: tuple[SurfaceMesh, ...]
    brep_payloads: tuple[BrepPayload, ...]
    diagnostics: tuple[Diagnostic, ...]
    capabilities: frozenset[Capability]


# the feature access contract needs a dedicated boundary so independent adapters agree on document semantics
class FeatureAccess:
    locals()["__slots__"] = ()

    # the feature timeline contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def FeatureTimeline(self) -> tuple[FeatureStep, ...]:
        return CastValue(FeatureFields, self).feature_timeline

    # the bodies contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def Bodies(self) -> tuple[DesignBody, ...]:
        return CastValue(FeatureFields, self).bodies

    # the meshes contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def Meshes(self) -> tuple[SurfaceMesh, ...]:
        return CastValue(FeatureFields, self).meshes

    # the boundary representation payloads contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def BrepPayloads(self) -> tuple[BrepPayload, ...]:
        return CastValue(FeatureFields, self).brep_payloads

    # the diagnostics contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def Diagnostics(self) -> tuple[Diagnostic, ...]:
        return CastValue(FeatureFields, self).diagnostics

    # the capabilities contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def Capabilities(self) -> frozenset[Capability]:
        return CastValue(FeatureFields, self).capabilities
