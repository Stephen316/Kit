from __future__ import annotations

from typing import Protocol, cast as CastValue

from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.mesh.SurfaceMesh import SurfaceMesh
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.records.RecordDiagnostic import Diagnostic


class FeatureFields(Protocol):
    feature_timeline: tuple[FeatureStep, ...]
    bodies: tuple[DesignBody, ...]
    meshes: tuple[SurfaceMesh, ...]
    brep_payloads: tuple[BrepPayload, ...]
    diagnostics: tuple[Diagnostic, ...]
    capabilities: frozenset[Capability]


class FeatureAccess:
    locals()["__slots__"] = ()

    @property
    def FeatureTimeline(self) -> tuple[FeatureStep, ...]:
        return CastValue(FeatureFields, self).feature_timeline

    @property
    def Bodies(self) -> tuple[DesignBody, ...]:
        return CastValue(FeatureFields, self).bodies

    @property
    def Meshes(self) -> tuple[SurfaceMesh, ...]:
        return CastValue(FeatureFields, self).meshes

    @property
    def BrepPayloads(self) -> tuple[BrepPayload, ...]:
        return CastValue(FeatureFields, self).brep_payloads

    @property
    def Diagnostics(self) -> tuple[Diagnostic, ...]:
        return CastValue(FeatureFields, self).diagnostics

    @property
    def Capabilities(self) -> frozenset[Capability]:
        return CastValue(FeatureFields, self).capabilities
