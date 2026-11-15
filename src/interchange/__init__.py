from interchange.materials.MaterialRecord import MaterialRecord
from dataclasses import is_dataclass as IsDataClass
from enum import Enum as EnumBase

from . import assembly as AssemblyModule
from . import brep as BrepModule
from . import document as DocumentModule
from . import geometry as GeometryModule
from . import history as HistoryModule
from . import mesh as MeshModule
from . import serialization as SerialModule
from . import types as TypesModule
from .types import (
    BooleanOperation,
    BoundingBox,
    CadSource,
    Capability,
    Configuration,
    ConstraintKind,
    Diagnostic,
    Expression,
    FeatureKind,
    GeometryKind,
    Parameter,
    ParameterOverride,
    ParameterRole,
    ParameterValue,
    Provenance,
    ProvenanceSpan,
    Severity,
    Transform,
    UnitSystem,
    ValueKind,
    Vector2 as LegacyVectorTwo,
    Vector3 as LegacyVectorThree,
    frozen_mapping as FrozenMapping,
)
from interchange.assembly.AssemblyData import AssemblyData
from interchange.assembly.AssemblyEnums import (
    ComponentKind,
    MateAlignment,
    MateEntityKind,
    MateKind,
)
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentDocument import ComponentDoc
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.assembly.TransformMatrix import TransformMatrix
from .brep import (
    BrepBody,
    BrepCoedge,
    BrepCurve,
    BrepEdge,
    BrepEntity,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepModel,
    BrepPcurve,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepSurface,
    BrepVertex,
    BrepWire,
    CircleCurve,
    CirclePcurve,
    ConeSurface,
    CylinderSurface,
    EllipseCurve,
    IntersectionCurve,
    LineCurve,
    LinePcurve,
    NativeCurve,
    NativePcurve,
    NativeSurface,
    NurbsCurve,
    NurbsPcurve,
    NurbsSurface,
    OffsetSurface,
    PlaneSurface,
    SphereSurface,
    TorusSurface,
)
from interchange.document.models.DocumentCaps import GetRetainedCaps, InferCaps
from interchange.document.models.DocumentError import DocumentError
from interchange.document.models.DocumentFilter import FilterDocument
from interchange.document.models.DocumentMetadata import AddWrapperMeta, GetSemanticMeta
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentPayload import GetPayloadIds
from interchange.enums.EnumDocument import Capability, Severity
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumGeometry import ConstraintKind, GeometryKind
from interchange.enums.EnumUnits import UnitSystem
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureContract import FeatureDef
from interchange.features.FeatureBoundPlane import BoundConstructionPlane
from interchange.features.FeatureBoundScale import BoundScale
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.features.FeatureKinds import (
    ChamferFeature,
    CirclePattern,
    CombineFeature,
    DomeFeature,
    FilletFeature,
    HoleFeature,
    LinearPattern,
    MoveBodyFeature,
    NativeFeature,
    RefPlaneFeature,
    RevolveFeature,
    ScaleFeature,
    ShellFeature,
)
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureCfgState, FeatureStep
from interchange.geometry.models.GeometryConics import (
    ArcEllipseGeom,
    ArcHyperGeom,
    ArcParabGeom,
    EllipseGeometry,
    HyperbolaGeom,
    ParabolaGeom,
)
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    NativeGeometry,
    PointGeometry,
    SplineGeometry,
)
from interchange.geometry.models.Selection import Selection, SelectPathElem
from interchange.geometry.models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.models.SupportPlane import SupportPlane
from .geometry.models.VectorPlane import PlaneVector
from .geometry.models.VectorSpace import SpaceVector
from .history import AdapterCaps
from interchange.mesh.SurfaceMesh import SurfaceMesh
from interchange.payloads.PayloadMigrate import MigratePayload
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.payloads.PayloadRoles import PayloadRole
from interchange.compatibility.PythonCompat import BindTypeGlobals
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Expression, Parameter, ParameterValue
from interchange.records.RecordProvenance import Provenance, ProvenanceSpan
from interchange.records.RecordSource import CadSource
from interchange.records.RecordTopology import TopologyCounts
from interchange.serialization.MigrationRegistry import RegMigration
from interchange.serialization.TypeRegistry import RegisterTypes
from interchange.geometry.models.Vectors import (
    BoundingBox,
    Transform,
)

# direct aliases make the runtime public contract visible to static analyzers
AdapterCapabilities = AdapterCaps

# the public arc ellipse geometry name must remain available so existing integrations keep resolving the canonical implementation
ArcEllipseGeometry = ArcEllipseGeom

# the public arc hyperbola geometry name must remain available so existing integrations keep resolving the canonical implementation
ArcHyperbolaGeometry = ArcHyperGeom

# the public arc parabola geometry name must remain available so existing integrations keep resolving the canonical implementation
ArcParabolaGeometry = ArcParabGeom

# the public body name must remain available so existing integrations keep resolving the canonical implementation
Body = DesignBody

# the public circular pattern feature name must remain available so existing integrations keep resolving the canonical implementation
CircularPatternFeature = CirclePattern

# the public component definition name must remain available so existing integrations keep resolving the canonical implementation
ComponentDefinition = ComponentDef

# the public component document name must remain available so existing integrations keep resolving the canonical implementation
ComponentDocument = ComponentDoc

# the public component instance name must remain available so existing integrations keep resolving the canonical implementation
ComponentInstance = ComponentInst

# the public constraint reference name must remain available so existing integrations keep resolving the canonical implementation
ConstraintReference = ConstraintRef

# the public cad document validation error name must remain available so existing integrations keep resolving the canonical implementation
CadDocumentValidationError = DocumentError

# the public extrusion end condition name must remain available so existing integrations keep resolving the canonical implementation
ExtrusionEndCondition = ExtrudeEnd

# the public extrusion feature name must remain available so existing integrations keep resolving the canonical implementation
ExtrusionFeature = ExtrudeFeature

# the public feature definition name must remain available so existing integrations keep resolving the canonical implementation
FeatureDefinition = FeatureDef

# the public feature configuration state name must remain available so existing integrations keep resolving the canonical implementation
FeatureConfigurationState = FeatureCfgState

# the public hyperbola geometry name must remain available so existing integrations keep resolving the canonical implementation
HyperbolaGeometry = HyperbolaGeom

# the public linear pattern feature name must remain available so existing integrations keep resolving the canonical implementation
LinearPatternFeature = LinearPattern

# the public matrix4 name must remain available so existing integrations keep resolving the canonical implementation
Matrix4 = TransformMatrix

# the public mesh name must remain available so existing integrations keep resolving the canonical implementation
Mesh = SurfaceMesh

# the public native feature definition name must remain available so existing integrations keep resolving the canonical implementation
NativeFeatureDefinition = NativeFeature

# the public parabola geometry name must remain available so existing integrations keep resolving the canonical implementation
ParabolaGeometry = ParabolaGeom

# the public reference plane feature name must remain available so existing integrations keep resolving the canonical implementation
ReferencePlaneFeature = RefPlaneFeature

# the public revolution feature name must remain available so existing integrations keep resolving the canonical implementation
RevolutionFeature = RevolveFeature

# the public selection path element name must remain available so existing integrations keep resolving the canonical implementation
SelectionPathElement = SelectPathElem

# the public sketch constraint name must remain available so existing integrations keep resolving the canonical implementation
SketchConstraint = SketchRelation

# the public topology summary name must remain available so existing integrations keep resolving the canonical implementation
TopologySummary = TopologyCounts

# the public vector2 name must remain available so existing integrations keep resolving the canonical implementation
Vector2 = LegacyVectorTwo

# the public vector3 name must remain available so existing integrations keep resolving the canonical implementation
Vector3 = LegacyVectorThree

# the public filter document name must remain available so existing integrations keep resolving the canonical implementation
filter_document = FilterDocument

# the public frozen mapping name must remain available so existing integrations keep resolving the canonical implementation
frozen_mapping = FrozenMapping

# the public infer capabilities name must remain available so existing integrations keep resolving the canonical implementation
infer_capabilities = InferCaps

# the public retained capabilities name must remain available so existing integrations keep resolving the canonical implementation
retained_capabilities = GetRetainedCaps

# the public register migration name must remain available so existing integrations keep resolving the canonical implementation
register_migration = RegMigration

# the public register types name must remain available so existing integrations keep resolving the canonical implementation
register_types = RegisterTypes

# the public semantic metadata name must remain available so existing integrations keep resolving the canonical implementation
semantic_metadata = GetSemanticMeta

# the public source payload indexes name must remain available so existing integrations keep resolving the canonical implementation
source_payload_indexes = GetPayloadIds

# the public with wrapper metadata name must remain available so existing integrations keep resolving the canonical implementation
with_wrapper_metadata = AddWrapperMeta

# the public assembly name must remain available so existing integrations keep resolving the canonical implementation
assembly = AssemblyModule

# the public boundary representation name must remain available so existing integrations keep resolving the canonical implementation
brep = BrepModule

# the public document name must remain available so existing integrations keep resolving the canonical implementation
document = DocumentModule

# the public geometry name must remain available so existing integrations keep resolving the canonical implementation
geometry = GeometryModule

# the public history name must remain available so existing integrations keep resolving the canonical implementation
history = HistoryModule

# the public mesh name must remain available so existing integrations keep resolving the canonical implementation
mesh = MeshModule

# the public serialization name must remain available so existing integrations keep resolving the canonical implementation
serialization = SerialModule

# the public types name must remain available so existing integrations keep resolving the canonical implementation
types = TypesModule

# package consumers need one intentional stable list of supported public symbols
__all__ = (
    "MaterialRecord",
    "AdapterCapabilities",
    "ArcEllipseGeometry",
    "ArcGeometry",
    "ArcHyperbolaGeometry",
    "ArcParabolaGeometry",
    "AssemblyData",
    "Body",
    "BooleanOperation",
    "BoundingBox",
    "BrepBody",
    "BrepCoedge",
    "BrepCurve",
    "BrepEdge",
    "BrepEntity",
    "BrepFace",
    "BrepFaceUse",
    "BrepLoop",
    "BrepModel",
    "BrepPayload",
    "BrepPcurve",
    "BrepRegion",
    "BrepShell",
    "BrepShellUse",
    "BrepSurface",
    "BrepVertex",
    "BrepWire",
    "CadDocument",
    "CadDocumentValidationError",
    "CadSource",
    "Capability",
    "ChamferFeature",
    "CircleCurve",
    "CircleGeometry",
    "CirclePcurve",
    "CircularPatternFeature",
    "CombineFeature",
    "ComponentDefinition",
    "ComponentDocument",
    "ComponentInstance",
    "ComponentKind",
    "Configuration",
    "ConeSurface",
    "ConstraintKind",
    "ConstraintReference",
    "CylinderSurface",
    "Diagnostic",
    "DomeFeature",
    "EllipseCurve",
    "EllipseGeometry",
    "Expression",
    "ExtrusionEndCondition",
    "ExtrusionFeature",
    "FeatureConfigurationState",
    "FeatureDefinition",
    "FeatureKind",
    "FeatureStep",
    "FilletFeature",
    "GeometryKind",
    "HoleFeature",
    "HyperbolaGeometry",
    "IntersectionCurve",
    "LineCurve",
    "LineGeometry",
    "LinePcurve",
    "LinearPatternFeature",
    "MateAlignment",
    "MateConstraint",
    "MateEntity",
    "MateEntityKind",
    "MateGroup",
    "MateKind",
    "Matrix4",
    "Mesh",
    "MoveBodyFeature",
    "NativeCurve",
    "NativeFeatureDefinition",
    "NativeGeometry",
    "NativePcurve",
    "NativeSurface",
    "NurbsCurve",
    "NurbsPcurve",
    "NurbsSurface",
    "OffsetSurface",
    "Parameter",
    "ParameterOverride",
    "ParameterRole",
    "ParameterValue",
    "ParabolaGeometry",
    "PayloadRole",
    "PlaneSurface",
    "PointGeometry",
    "PlaneVector",
    "Provenance",
    "ProvenanceSpan",
    "ReferencePlaneFeature",
    "RevolutionFeature",
    "ScaleFeature",
    "Selection",
    "SelectionPathElement",
    "Severity",
    "ShellFeature",
    "Sketch",
    "SketchConstraint",
    "SketchEntity",
    "SphereSurface",
    "SplineGeometry",
    "SupportPlane",
    "SpaceVector",
    "TopologySummary",
    "TorusSurface",
    "Transform",
    "UnitSystem",
    "ValueKind",
    "Vector2",
    "Vector3",
    "assembly",
    "brep",
    "document",
    "filter_document",
    "frozen_mapping",
    "geometry",
    "history",
    "infer_capabilities",
    "mesh",
    "register_migration",
    "register_types",
    "retained_capabilities",
    "semantic_metadata",
    "serialization",
    "source_payload_indexes",
    "with_wrapper_metadata",
    "types",
)

BindTypeGlobals(
    (
        AssemblyModule,
        BrepModule,
        DocumentModule,
        GeometryModule,
        HistoryModule,
        MeshModule,
        TypesModule,
    ),
    tuple(
        # nosemgrep: python.lang.security.dangerous-globals-use.dangerous-globals-use
        globals()[NameValue]
        for NameValue in __all__
        # nosemgrep: python.lang.security.dangerous-globals-use.dangerous-globals-use
        if isinstance(globals()[NameValue], type)
    ),
)

RegisterTypes(
    AngularRevolve,
    BoundConstructionPlane,
    BoundScale,
    DistanceExtrude,
    PlaneExtrude,
    PlaneRevolve,
    *(
        # nosemgrep: python.lang.security.dangerous-globals-use.dangerous-globals-use
        globals()[NameValue]
        for NameValue in __all__
        # nosemgrep: python.lang.security.dangerous-globals-use.dangerous-globals-use
        if isinstance(globals()[NameValue], type)
        and (
            # nosemgrep: python.lang.security.dangerous-globals-use.dangerous-globals-use
            IsDataClass(globals()[NameValue])
            # nosemgrep: python.lang.security.dangerous-globals-use.dangerous-globals-use
            or issubclass(globals()[NameValue], EnumBase)
        )
    ),
)

RegMigration(BrepPayload, MigratePayload)
