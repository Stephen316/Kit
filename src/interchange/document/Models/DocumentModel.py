from __future__ import annotations

from interchange.document.Models.Access.RootAccess import RootAccess
from interchange.document.Models.Access.FeatureAccess import FeatureAccess
from interchange.document.Models.Access.GeometryAccess import GeometryAccess

from dataclasses import dataclass as MakeDataClass
from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap
from typing import cast as CastValue

from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.GraphView import GraphView
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Core.Common import FreezeMapping
from interchange.Core.ModelBase import ModelBase, ModelDataMut
from interchange.Core.ModelExtras import ModelExtras
from interchange.document.Behavior.DocumentBehavior import DocumentApi
from interchange.document.Models.DocumentRoot import DocumentRoot
from interchange.Enums.EnumDocument import Capability
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.materials.MaterialRecord import MaterialRecord
from interchange.mesh.SurfaceMesh import SurfaceMesh
from interchange.Payloads.PayloadRecord import BrepPayload
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordDiagnostic import Diagnostic
from interchange.Records.RecordParameter import Parameter
from interchange.Records.RecordSource import CadSource


# portable cad exchange needs one immutable root connecting every neutral model domain
@MakeDataClass(frozen=True, slots=True)
class CadDocument(
    DocumentRoot, DocumentApi, RootAccess, FeatureAccess, GeometryAccess, ModelBase
):
    source: CadSource
    configurations: tuple[Configuration, ...]
    parameters: tuple[Parameter, ...]
    support_planes: tuple[SupportPlane, ...]
    sketches: tuple[Sketch, ...]
    selections: tuple[Selection, ...]
    feature_timeline: tuple[FeatureStep, ...]
    bodies: tuple[DesignBody, ...]
    meshes: tuple[SurfaceMesh, ...] = ()
    brep_payloads: tuple[BrepPayload, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    capabilities: frozenset[Capability] = frozenset()
    metadata: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
    units: UnitSystem = UnitSystem.KMillimeter
    schema_version: str = "1.0"
    assembly: AssemblyData | None = None
    brep: BrepModel | None = None
    materials: tuple[MaterialRecord, ...] = ()

    # the assembly contract needs a shared interpretation so independent adapters agree on document semantics
    @property
    def Assembly(self) -> AssemblyData | None:
        return self.assembly


# component documents embed linked portable documents without weakening graph typing
@ModelDataMut
class ComponentDoc(ModelBase):
    id: str
    document: CadDocument

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

    # underlying document access keeps assembly views decoupled from storage internals
    @property
    def Document(self) -> CadDocument:
        return self.document


# assembly definition lookups stay separable because graph views compose without owning storage
class DefLookupView(GraphView):
    locals()["__slots__"] = ()

    # definition lookup gives callers one consistent missing identifier failure mode
    def GetDefinition(self, EntityId: str) -> ComponentDef:
        StoredDefinitions = CastValue(
            tuple[ComponentDef, ...],
            getattr(self, "definitions"),
        )
        for DefinitionValue in StoredDefinitions:
            if DefinitionValue.id == EntityId:
                return DefinitionValue
        raise KeyError(f"unknown component definition id {EntityId!r}")

    # pascal lookup keeps one canonical spelling because compatibility wrappers need twins
    def Definition(self, EntityId: str) -> ComponentDef:
        return self.GetDefinition(EntityId)

    # lowercase lookup stays concrete because static consumers cannot observe runtime aliases
    def definition(self, entity_id: str) -> ComponentDef:
        return self.GetDefinition(entity_id)

    # pascal child ordering keeps one canonical spelling because compatibility wrappers need twins
    def Children(self, DefinitionId: str) -> tuple[ComponentInst, ...]:
        return self.GetChildren(DefinitionId)

    # lowercase child ordering stays concrete because static consumers cannot observe runtime aliases
    def children(self, definition_id: str) -> tuple[ComponentInst, ...]:
        return self.GetChildren(definition_id)


# assembly document lookups stay separable because linked records resolve without storage coupling
class DocLookupView:
    locals()["__slots__"] = ()

    # document list keeps external references inspectable without reopening files
    @property
    def Documents(self) -> "tuple[ComponentDoc, ...]":
        return CastValue("tuple[ComponentDoc, ...]", getattr(self, "documents"))

    # embedded document lookup avoids exposing storage details to assembly consumers
    def GetDocument(self, EntityId: str) -> CadDocument:
        StoredDocuments = CastValue(
            tuple[ComponentDoc, ...],
            getattr(self, "documents"),
        )
        for DocumentValue in StoredDocuments:
            if DocumentValue.id == EntityId:
                return DocumentValue.document
        raise KeyError(f"unknown component document id {EntityId!r}")

    # pascal lookup keeps one canonical spelling because compatibility wrappers need twins
    def Document(self, EntityId: str) -> CadDocument:
        return self.GetDocument(EntityId)

    # lowercase lookup stays concrete because linked document consumers need its exact return type
    def document(self, entity_id: str) -> CadDocument:
        return self.GetDocument(entity_id)


# assembly data composes occurrences documents and mates into one portable graph
@ModelDataMut
class AssemblyData(DefLookupView, DocLookupView, ModelExtras, ModelBase):
    root_definition_id: str
    definitions: tuple[ComponentDef, ...]
    instances: tuple[ComponentInst, ...]
    documents: tuple[ComponentDoc, ...] = ()
    mate_entities: tuple[MateEntity, ...] = ()
    mates: tuple[MateConstraint, ...] = ()
    mate_groups: tuple[MateGroup, ...] = ()
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
