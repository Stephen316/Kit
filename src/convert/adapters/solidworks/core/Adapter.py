from __future__ import annotations as Annotations
from collections import defaultdict as Defaultdict
from contextlib import suppress as Suppress
from dataclasses import dataclass as DataClass, replace as Replace
import hashlib as Hashlib
from io import BytesIO as BytesIo
import json as JsonValue
import math as MathValue
import os as OsModule
from pathlib import Path as FilePath, PureWindowsPath
import re as RegexLib
import struct as Struct
import tempfile as Tempfile
from typing import Mapping, Sequence

from convert.adapters.base import (
    AdapterInfo,
    ProbeResult,
    ReadOptions,
    Source,
    is_binary_destination as IsBinaryTarget,
)
from interchange import (
    ArcEllipseGeometry as ArcEllipseGeom,
    ArcGeometry as ArcGeom,
    ArcParabolaGeometry as ArcParabolaGeom,
    AssemblyData as AsmData,
    Body as BodyValue,
    BooleanOperation as BoolOperation,
    BoundingBox,
    BrepModel,
    BrepPayload,
    CadDocument as CadDoc,
    CadSource,
    ChamferFeature,
    CircleGeometry as CircleGeom,
    CombineFeature,
    ComponentDefinition,
    ComponentDocument as ComponentDoc,
    ComponentInstance,
    ComponentKind,
    Configuration as Config,
    ConstraintReference as RuleRef,
    Diagnostic as DiagValue,
    DomeFeature,
    ExtrusionEndCondition,
    ExtrusionFeature,
    Expression,
    EllipseGeometry as EllipseGeom,
    FeatureKind,
    FeatureStep,
    FilletFeature,
    GeometryKind as GeomKind,
    HoleFeature,
    LineGeometry as LineGeom,
    MateAlignment,
    MateConstraint as MateRule,
    MateEntity,
    MateEntityKind,
    MateGroup,
    MateKind,
    Matrix4 as MatrixFour,
    Mesh as MeshValue,
    MoveBodyFeature,
    NativeFeatureDefinition,
    NativeGeometry as NativeGeom,
    Parameter as Param,
    ParameterRole as ParamRole,
    ParameterValue as ParamValue,
    PointGeometry as PointGeom,
    PayloadRole,
    Provenance,
    ProvenanceSpan,
    ReferencePlaneFeature as RefPlaneFeature,
    RevolutionFeature,
    ScaleFeature,
    Selection,
    SelectionPathElement as SelectionPathElem,
    Severity,
    ShellFeature,
    Sketch as SketchData,
    SketchConstraint as SketchRule,
    SketchEntity,
    SplineGeometry as SplineGeom,
    SupportPlane,
    TopologySummary,
    Transform,
    UnitSystem,
    ValueKind,
    Vector2 as VectorTwo,
    Vector3 as VectorThree,
    frozen_mapping as FrozenMapping,
    filter_document as FilterDoc,
    infer_capabilities as InferCapabilities,
    retained_capabilities as RetainedCapabilities,
    semantic_metadata as SemanticMeta,
    source_payload_indexes as SourcePayloadIndexes,
    with_wrapper_metadata as WithWrapperMeta,
)
from convert.adapters.solidworks.assembly.Assembly import (
    MATE_VALUE_SEMANTICS as MateValueSemantics,
    NATIVE_MATE_ALIGNMENT_BY_CODE as NativeMateAlignmentByCode,
    NATIVE_MATE_ENTITY_MARKERS as NativeMateEntityMarkers,
    NATIVE_MATE_NEUTRAL_KIND_ALIASES as NativeMateNeutralKind,
    NativeAssembly as NativeAsm,
    NativeAssemblyDefinition as NativeAsmDefinition,
    NativeAssemblyOccurrence as NativeAsmItem,
    NativeMate,
    NativeMateEntity,
    NativeMateList,
    decode_mate_list as DecodeMateList,
    decode_native_assembly as DecodeNativeAsm,
)
from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
    SldprtFormatError,
    build_sldprt as BuildSldprt,
)
from convert.adapters.solidworks.container.Format import (
    COMPONENT_TREE_STREAM as ComponentTreeStream,
    CONTAINER_VERSIONS as ContainerVersions,
    CONTENT_TYPES_STREAM as ContentTypesStream,
    DISPLAY_LISTS_STREAM as DisplayListsStream,
    FORMAT_ID_BY_SUFFIX as FormatIdBySuffix,
    INFO as InfoValue,
    KEYWORDS_STREAM as KeywordsStream,
    KIT_DOCUMENT_STREAM as KitDocStream,
    KIT_RESOLVED_STREAM as KitResolvedStream,
    MATES_STREAM_NAME as MatesStreamName,
    MATES_STREAM_SUFFIX as MatesStreamSuffix,
    PLANE_FEATURE_TYPES as PlaneFeatureTypes,
    RELATIONSHIPS_STREAM as RelationshipsStream,
    RESOLVED_FEATURES_STREAM as ResolvedFeaturesStream,
    SOLID_BODY_FEATURE_TYPES as SolidBodyFeatureTypes,
    SUFFIX_BY_FORMAT_ID as SuffixByFormatId,
)
from convert.adapters.solidworks.core.FeatureKindByNative import KFeatureKindByNative
from convert.adapters.solidworks.core.AxisSketchId import AxisSketchId
from convert.adapters.solidworks.core.BuildRevolve import BuildRevolve as BuildRevolve
from convert.adapters.solidworks.core.SketchIdentity import (
    MarkerId as MarkerId,
)
from convert.adapters.solidworks.core.Display import NativeDisplay
from convert.adapters.solidworks.core.Native import (
    NativeDimension,
    NativeFeature,
    XmlFeature,
    NativeMarker,
    NativeModel,
    NativeOperation,
    NativePlane,
    NativeProfile,
    NativeRule,
    NativeSketch,
    DIRECTION_AXIS_ROLE as DirectionAxisRole,
    decode_native_model as DecodeNativeModel,
    operation_axis_subelement as OperationAxisSubElem,
)
from interchange.geometry.models.GeometryTypes import KGeometryTypes
from convert.adapters.solidworks.container.Parasolid import (
    ParasolidPayload,
    contains_parasolid_payload as ContainsParasolidPayload,
    decode_brep_model as DecodeBrepModel,
    decode_partition_stream as DecodePartitionStream,
    encode_blank_partition_stream as EncodeBlankPartition,
    encode_brep_model as EncodeBrepModel,
    encode_partition_stream as EncodePartitionStream,
    is_native_parasolid_payload as IsNativeParasolidPayload,
)

# this binding exists because shared behavior needs one stable value
KFormatId = InfoValue.format_id

# this binding exists because shared behavior needs one stable value
KAsmFormatId = InfoValue.aliases[0]

# this binding exists because shared behavior needs one stable value
KSourceBytesKey = "solidworks_source_bytes"

# this binding exists because shared behavior needs one stable value
KSourceShaTwoFiveSixKey = "solidworks_source_sha256"

# this binding exists because shared behavior needs one stable value
KSourceSemanticShaTwoFive = "solidworks_source_semantic_sha256"

# this binding exists because shared behavior needs one stable value
KSourceFormatKey = "solidworks_source_format_id"


# this binding exists because shared behavior needs one stable value
KSourceKeys = frozenset(
    {
        KSourceBytesKey,
        KSourceShaTwoFiveSixKey,
        KSourceSemanticShaTwoFive,
        KSourceFormatKey,
    }
)


# this binding exists because shared behavior needs one stable value
KResolvedConfigStream = RegexLib.compile("^Contents/Config-(\\d+)-ResolvedFeatures$")


# this binding exists because shared behavior needs one stable value
KWrapperMetaKeys = KSourceKeys | frozenset(
    {
        "adapter",
        "embedded_source_format_id",
        "embedded_source_path",
        "embedded_source_sha256",
        "file_id",
        "solidworks.container_compatibility",
        "stream_names",
    }
)


# compat protocol marker exempts paired wrappers from naming constraints
class PairProtocol:

    KSlotsValue = ()

    locals()["__slots__"] = KSlotsValue


# sldprt adapter keeps the historical surface because callers depend on it directly
class SldprtAdapter(PairProtocol):
    __slots__ = ()

    # adapter discovery needs metadata before callers probe or convert source documents
    @property
    def info(self) -> AdapterInfo:
        return InfoAction(self)

    # source assessment stays non destructive because probing precedes any conversion commitment
    def probe(self, SourceValue: Source) -> ProbeResult:
        return Probe(self, SourceValue)

    # conversion needs one neutral document result across solidworks reader implementations
    def read(self, SourceValue: Source, Options: ReadOptions | None = None) -> CadDoc:
        return ReadAction(self, SourceValue, Options)


# adapter metadata stays isolated so discovery can inspect capabilities without reading documents
def InfoAction(Instance: SldprtAdapter) -> AdapterInfo:
    return InfoValue


# probing stays independent so format detection never performs a full conversion
def Probe(Instance: SldprtAdapter, Source: Source) -> ProbeResult:
    try:
        DataValue, Label = SourceBytes(Source)
        if len(DataValue) < 8:
            return ProbeResult(
                KFormatId, 0.0, "file is shorter than the container header"
            )
        Version = Struct.unpack_from(">I", DataValue, 4)[0]
        if Version not in ContainerVersions:
            return ProbeResult(
                KFormatId, 0.0, f"unsupported container version {Version}"
            )
        Archive = SldprtArchive.from_bytes(DataValue, Label)
    except (OSError, SldprtFormatError, TypeError, ValueError) as ErrorInfo:
        return ProbeResult(KFormatId, 0.0, str(ErrorInfo))
    Names = Archive.streams
    if KeywordsStream in Names and any(
        (KResolvedConfigStream.fullmatch(NameValue) for NameValue in Names)
    ):
        return ProbeResult(
            KFormatId, 1.0, "native history and resolved-feature streams found"
        )
    return ProbeResult(
        KFormatId, 0.6, "recognized SOLIDWORKS compound stream container"
    )


# adapter reading dispatches embedded assembly and native part paths through one contract
def ReadAction(
    Instance: SldprtAdapter, Source: Source, Options: ReadOptions | None = None
) -> CadDoc:
    Settings = Options or ReadOptions()
    DataValue, Label = SourceBytes(Source)
    Archive = SldprtArchive.from_bytes(DataValue, Label)
    Embedded = Archive.get(KitDocStream)
    if Embedded is not None:
        DocValue = EmbeddedDoc(Instance, Archive, DataValue, Label, Embedded, Settings)
        ValidateSource(Label, DocValue.assembly is not None)
        return DocValue
    if Archive.get(ComponentTreeStream) is not None:
        DocValue = RetainSource(
            AsmDoc(Instance, Archive, DataValue, Label, Settings), DataValue
        )
        ValidateSource(Label, True)
        return DocValue
    return ReadNativePart(Instance, Archive, DataValue, Label, Settings)


# native part reconstruction stays separate because assembly and embedded documents bypass this model path
def ReadNativePart(
    Instance: SldprtAdapter,
    Archive: SldprtArchive,
    DataValue: bytes,
    Label: str,
    Settings: ReadOptions,
) -> CadDoc:
    Model = NativePartModel(Archive, Settings.configuration)
    ConfigValues = Configurations(Model, Settings.configuration)
    ParamValues = Parameters(Model)
    ParamIds = {Param.id for Param in ParamValues}
    PlaneValues = Planes(Model, ParamIds)
    SketchValues = Sketches(Model, ParamIds)
    SelectValues = Selections(Model)
    TimeValues = Timeline(Model, SelectValues)
    Payloads, PayloadDiags = BrepPayloads(Archive, Settings)
    BrepValue = TypedBrep(Payloads)
    SolidOpIds = frozenset(
        (
            FeatureId(Operation.object_id)
            for Operation in Model.operations
            if Operation.kind != "surface"
        )
    )
    FinalFeature = FinalBodyId(TimeValues, SolidOpIds)
    BodyFeature = SolidBody(Model.features)
    Bodies = (
        BodyValue(
            id="sldprt:body:1",
            name=BodyFeature.name if BodyFeature is not None else "Body 1",
            final_feature_id=FinalFeature,
            topology=TopologySummary(
                solid_count=1 if SolidOpIds else 0, bounding_box=BoundingBoxA(Model)
            ),
            provenance=FeatureA(BodyFeature) if BodyFeature is not None else None,
            attributes=FrozenMapping(
                {
                    "native_object_id": (
                        BodyFeature.object_id if BodyFeature is not None else None
                    ),
                    "parasolid_payload_ids": tuple(
                        (Payload.id for Payload in Payloads)
                    ),
                }
            ),
        ),
    )
    Diagnostics = (
        tuple(
            (
                DiagValue(
                    code="sldprt.native_record_unresolved",
                    message=Message,
                    severity=Severity.INFO,
                )
                for Message in Model.diagnostics
            )
        )
        + PayloadDiags
    )
    DocValue = CadDoc(
        source=CadSource(
            format_id=KFormatId,
            path=Label,
            sha256=Hashlib.sha256(DataValue).hexdigest(),
            container_version=str(Archive.format_version),
            attributes=FrozenMapping(
                {"file_id": Archive.file_id, "stream_count": len(Archive.records)}
            ),
        ),
        configurations=ConfigValues,
        parameters=ParamValues,
        support_planes=PlaneValues,
        sketches=SketchValues,
        selections=SelectValues,
        feature_timeline=TimeValues,
        bodies=Bodies,
        brep=BrepValue,
        brep_payloads=Payloads,
        diagnostics=Diagnostics,
        capabilities=Instance.info.capabilities,
        metadata=FrozenMapping(
            {
                "adapter": KFormatId,
                "file_id": Archive.file_id,
                "native_class_names": tuple(
                    dict.fromkeys((ItemValue.name for ItemValue in Model.classes))
                ),
                "native_feature_count": len(Model.features),
                "native_name_record_count": len(Model.names),
                "native_scalar_count": len(Model.scalars),
                "stream_names": tuple((Record.name for Record in Archive.records)),
            }
        ),
        units=UnitSystem.MILLIMETER,
    )
    DocValue.assert_valid()
    ValidateSource(Label, False)
    return RetainSource(DocValue, DataValue)


# boolean option validation keeps compatibility keywords aligned with canonical options
def IsBoolValue(Value: object, FieldName: str) -> bool:
    if not isinstance(Value, bool):
        raise TypeError(f"{FieldName} must be a boolean")
    return Value


# optional text validation keeps compatibility keywords aligned with canonical options
def OptionalString(Value: object, FieldName: str) -> str | None:
    if Value is not None and not isinstance(Value, str):
        raise TypeError(f"{FieldName} must be a string or None")
    return Value


# this definition exists because focused behavior needs one stable owner
def ReadSldprt(
    Source: Source,
    *,
    Config: str | None = None,
    IncludeBrep: bool = True,
    IncludeTessellation: bool = True,
    Strict: bool = True,
    **LegacyValues: object,
) -> CadDoc:
    Config = OptionalString(LegacyValues.get("configuration", Config), "configuration")
    IncludeBrep = IsBoolValue(
        LegacyValues.get("include_brep", IncludeBrep), "include_brep"
    )
    IncludeTessellation = IsBoolValue(
        LegacyValues.get("include_tessellation", IncludeTessellation),
        "include_tessellation",
    )
    Strict = IsBoolValue(LegacyValues.get("strict", Strict), "strict")
    UnknownValues = set(LegacyValues) - {
        "configuration",
        "include_brep",
        "include_tessellation",
        "strict",
    }
    if UnknownValues:
        Unexpected = next(iter(UnknownValues))
        raise TypeError(
            f"ReadSldprt() got an unexpected keyword argument {Unexpected!r}"
        )
    return SldprtAdapter().read(
        Source,
        ReadOptions(
            configuration=Config,
            include_brep=IncludeBrep,
            include_tessellation=IncludeTessellation,
            strict=Strict,
        ),
    )


# this definition exists because focused behavior needs one stable owner
def EmbeddedDoc(
    Adapter: SldprtAdapter,
    Archive: SldprtArchive,
    DataValue: bytes,
    Label: str,
    Embedded: bytes,
    Settings: ReadOptions,
) -> CadDoc:
    try:
        DocValue = CadDoc.from_json(Embedded.decode("utf-8"))
    except (UnicodeDecodeError, TypeError, ValueError) as ErrorInfo:
        raise SldprtFormatError("embedded Kit document is invalid") from ErrorInfo
    Configurations = DocValue.configurations
    if Settings.configuration is not None:
        Matches = {
            ItemValue.id
            for ItemValue in Configurations
            if Settings.configuration in {ItemValue.id, ItemValue.name}
        }
        if not Matches:
            raise SldprtFormatError(
                f"configuration {Settings.configuration!r} is unavailable"
            )
        Configurations = tuple(
            (
                Replace(ItemValue, active=ItemValue.id in Matches)
                for ItemValue in Configurations
            )
        )
    Original = DocValue.source
    FormatId = KAsmFormatId if DocValue.assembly is not None else KFormatId
    MetaValue = dict(DocValue.metadata)
    MetaValue.update(
        {
            "adapter": FormatId,
            "file_id": Archive.file_id,
            "stream_names": tuple((Record.name for Record in Archive.records)),
            "embedded_source_format_id": Original.format_id,
            "embedded_source_path": Original.path,
            "embedded_source_sha256": Original.sha256,
            "solidworks.container_compatibility": Replay(DataValue),
        }
    )
    DocValue = Replace(
        DocValue,
        source=CadSource(
            format_id=FormatId,
            path=Label,
            sha256=Hashlib.sha256(DataValue).hexdigest(),
            container_version=str(Archive.format_version),
            attributes=FrozenMapping(
                {
                    "file_id": Archive.file_id,
                    "stream_count": len(Archive.records),
                    "embedded_source_format_id": Original.format_id,
                }
            ),
        ),
        configurations=Configurations,
        metadata=FrozenMapping(MetaValue),
    )
    DocValue = FilterDoc(
        DocValue,
        include_brep=Settings.include_brep,
        include_tessellation=Settings.include_tessellation,
        keep_payload_records=False,
    )
    if Settings.strict:
        DocValue.assert_valid()
    return RetainSource(
        DocValue, DataValue, RetainCapabilities=True, OptionsValue=Settings
    )


# this definition exists because focused behavior needs one stable owner
def DocWithout(DocValue: CadDocument) -> CadDoc:
    return Replace(
        DocValue,
        metadata=FrozenMapping(
            {
                KeyValue: Value
                for KeyValue, Value in DocValue.metadata.items()
                if KeyValue not in KSourceKeys
            }
        ),
    )


# this definition exists because focused behavior needs one stable owner
def SemanticShaTwo(DocValue: CadDocument) -> str:
    Value = SemanticDoc(DocValue).to_json(indent=None).encode("utf-8")
    return Hashlib.sha256(Value).hexdigest()


# this definition exists because focused behavior needs one stable owner
def SemanticDoc(DocValue: CadDocument) -> CadDoc:
    EnvelopeIndexes = SourcePayloadIndexes(DocValue)
    Payloads = tuple(
        (
            Replace(
                Payload,
                data=None,
                sha256=(
                    Hashlib.sha256(Payload.data).hexdigest()
                    if Payload.data is not None
                    else Payload.sha256
                ),
            )
            for Index, Payload in enumerate(DocValue.brep_payloads)
            if Index not in EnvelopeIndexes
        )
    )
    AsmValue = DocValue.assembly
    if AsmValue is not None:
        AsmValue = Replace(
            AsmValue,
            documents=tuple(
                (
                    Replace(
                        ItemValue,
                        document=SemanticDoc(ItemValue.document),
                    )
                    for ItemValue in AsmValue.documents
                )
            ),
        )
    return Replace(
        DocValue,
        source=CadSource("", "", ""),
        brep_payloads=Payloads,
        metadata=SemanticMeta(DocValue.metadata),
        assembly=AsmValue,
    )


# this definition exists because focused behavior needs one stable owner
def RetainSource(
    DocValue: CadDocument,
    DataValue: bytes,
    *,
    RetainCapabilities: bool = False,
    OptionsValue: ReadOptions | None = None,
) -> CadDoc:
    Capabilities = DocValue.capabilities
    SelectedOptions = OptionsValue or ReadOptions()
    Portable = DocWithout(DocValue)
    Portable = Replace(
        Portable, metadata=WithWrapperMeta(Portable.metadata, KWrapperMetaKeys)
    )
    SelectedCapabilities = (
        RetainedCapabilities(
            Portable,
            Capabilities,
            include_brep=SelectedOptions.include_brep,
            include_tessellation=SelectedOptions.include_tessellation,
        )
        if RetainCapabilities
        else InferCapabilities(Portable, roundtrip_metadata=True)
    )
    Portable = Replace(Portable, capabilities=SelectedCapabilities)
    MetaValue = dict(Portable.metadata)
    MetaValue.update(
        {
            KSourceBytesKey: bytes(DataValue),
            KSourceShaTwoFiveSixKey: Hashlib.sha256(DataValue).hexdigest(),
            KSourceSemanticShaTwoFive: SemanticShaTwo(Portable),
            KSourceFormatKey: DocValue.source.format_id,
        }
    )
    return Replace(Portable, metadata=WithWrapperMeta(MetaValue, KWrapperMetaKeys))


# this definition exists because focused behavior needs one stable owner
def IsGeomBrep(Payload: BrepPayload) -> bool:
    return Payload.role == PayloadRole.BREP and Payload.data is not None


# this definition exists because focused behavior needs one stable owner
def Replay(DataValue: bytes) -> str:
    Archive = SldprtArchive.from_bytes(DataValue)
    if KitDocStream not in Archive.streams:
        return "native-exact"
    return "kit-neutral-only"


# this definition exists because assembly part metadata shares one decode pass
def AsmPartFields(Archive: SldprtArchive, Settings: ReadOptions) -> tuple[
    NativeModel,
    tuple[Config, ...],
    tuple[Param, ...],
    tuple[SupportPlane, ...],
    tuple[SketchData, ...],
    tuple[Selection, ...],
    tuple[FeatureStep, ...],
]:
    SelectedStream = ResolvedStream(Archive.streams, ResolvedFeaturesStream)
    Model = DecodeNativeModel(
        Archive.require(KeywordsStream),
        Archive.require(SelectedStream),
        resolved_stream=SelectedStream,
    )
    ConfigValues = Configurations(Model, Settings.configuration)
    ParamValues = Parameters(Model)
    ParamIds = {Param.id for Param in ParamValues}
    PlaneValues = Planes(Model, ParamIds)
    SketchValues = Sketches(Model, ParamIds)
    SelectValues = Selections(Model)
    TimeValues = Timeline(Model, SelectValues)
    return (
        Model,
        ConfigValues,
        ParamValues,
        PlaneValues,
        SketchValues,
        SelectValues,
        TimeValues,
    )


# this definition exists because focused behavior needs one stable owner
def AsmDoc(
    Adapter: SldprtAdapter,
    Archive: SldprtArchive,
    DataValue: bytes,
    Label: str,
    Settings: ReadOptions,
) -> CadDoc:
    Native = DecodeNativeAsm(Archive, include_tessellation=True)
    (
        Model,
        ConfigValues,
        ParamValues,
        PlaneValues,
        SketchValues,
        SelectValues,
        TimeValues,
    ) = AsmPartFields(Archive, Settings)
    Meshes, MeshIds = AsmMeshes(Native)
    Index = ComponentFile(Label, Settings)
    ResolveComponents = Settings.values.get("resolve_components", True) is not False
    Documents, DocIds, ResolvedPaths, DocDiagnostics = AsmDocuments(
        Adapter, Native, Index if ResolveComponents else {}, Settings
    )
    Definitions = AsmDefinitions(
        Native,
        DocIds,
        ResolvedPaths,
        {DocValue.id: DocValue.document for DocValue in Documents},
        MeshIds,
        Label,
    )
    Instances = AsmInstances(Native)
    MateSourceValues, SourceDiagnostics = MateSources(
        Native, Archive, Label, Index, Settings
    )
    MatePayloads, MateEntities, Mates, MateGroups = AsmMates(Native, MateSourceValues)
    FlatMateValues = FlattenedMates(Native, Mates)
    PayloadSettings = ReadOptions(
        configuration=Settings.configuration,
        include_brep=Settings.include_brep,
        include_tessellation=Settings.include_tessellation,
        strict=False,
        values=Settings.values,
    )
    BrepValues, PayloadDiagnostics = BrepPayloads(Archive, PayloadSettings)
    CompanionPayloads = (
        Companion(Label)
        if Settings.include_brep
        and Settings.values.get("discover_companions", True) is not False
        else ()
    )
    Unresolved = tuple(
        (
            Definition
            for Definition in Native.definitions
            if Definition.document_type == "PART"
            and Definition.object_id not in DocIds
            and (Definition.object_id not in MeshIds)
        )
    )
    if Unresolved and Settings.strict and ResolveComponents:
        Names = ", ".join((Definition.name for Definition in Unresolved))
        raise SldprtFormatError(
            f"assembly component sources and tessellation are unavailable: {Names}"
        )
    Diagnostics = (
        tuple(
            (
                DiagValue(
                    code="sldasm.native_record_unresolved",
                    message=Message,
                    severity=Severity.INFO,
                )
                for Message in Model.diagnostics
            )
        )
        + PayloadDiagnostics
        + DocDiagnostics
        + SourceDiagnostics
    )
    PathRecords = Flattened(Native)
    LinkedDocuments = {DocValue.id: DocValue.document for DocValue in Documents}
    LinkedPartDocuments = tuple(
        (
            DocValue
            for DocValue in Documents
            if DocValue.document.source.format_id == KFormatId
        )
    )
    LinkedAsmDocuments = tuple(
        (
            DocValue
            for DocValue in Documents
            if DocValue.document.source.format_id == KAsmFormatId
        )
    )
    AsmValue = AsmData(
        root_definition_id=AsmDefinitionId(Native.root_definition_id),
        definitions=Definitions,
        instances=Instances,
        documents=Documents,
        mate_entities=MateEntities,
        mates=Mates,
        mate_groups=MateGroups,
        attributes=FrozenMapping(
            {
                "application_version": Native.application_version,
                "configurations": tuple(
                    (
                        {
                            "native_object_id": Config.object_id,
                            "native_configuration_id": Config.configuration_id,
                            "name": Config.name,
                            "reference": Config.reference,
                            "model_id": Config.model_id,
                            "most_recent": Config.most_recent,
                            "needs_update": Config.needs_update,
                            "native_attributes": Config.attributes,
                        }
                        for Config in Native.configurations
                    )
                ),
                "display_states": tuple(
                    (
                        {
                            "native_object_id": State.object_id,
                            "name": State.name,
                            "configuration_id": State.configuration_id,
                            "native_attributes": State.attributes,
                        }
                        for State in Native.display_states
                    )
                ),
                "flattened_occurrences": PathRecords,
                "flattened_occurrence_count": len(PathRecords),
                "flattened_mate_occurrences": FlatMateValues,
                "flattened_mate_occurrence_count": len(FlatMateValues),
                "native_file_count": len(Native.files),
                "native_definition_count": len(Native.definitions),
                "native_instance_count": len(Native.occurrences),
                "linked_document_count": len(Documents),
                "linked_part_document_count": len(LinkedPartDocuments),
                "linked_assembly_document_count": len(LinkedAsmDocuments),
                "linked_sketch_count": sum(
                    (len(DocValue.sketches) for DocValue in LinkedDocuments.values())
                ),
                "linked_feature_count": sum(
                    (
                        len(DocValue.feature_timeline)
                        for DocValue in LinkedDocuments.values()
                    )
                ),
            }
        ),
    )
    DocValue = CadDoc(
        source=CadSource(
            format_id=KAsmFormatId,
            path=Label,
            sha256=Hashlib.sha256(DataValue).hexdigest(),
            container_version=str(Archive.format_version),
            application_version=str(Native.application_version),
            attributes=FrozenMapping(
                {"file_id": Archive.file_id, "stream_count": len(Archive.records)}
            ),
        ),
        configurations=ConfigValues,
        parameters=ParamValues,
        support_planes=PlaneValues,
        sketches=SketchValues,
        selections=SelectValues,
        feature_timeline=TimeValues,
        bodies=(),
        meshes=Meshes,
        brep_payloads=(*BrepValues, *MatePayloads, *CompanionPayloads),
        diagnostics=Diagnostics,
        capabilities=Adapter.info.capabilities,
        metadata=FrozenMapping(
            {
                "adapter": KAsmFormatId,
                "file_id": Archive.file_id,
                "native_class_names": tuple(
                    dict.fromkeys((ItemValue.name for ItemValue in Model.classes))
                ),
                "native_feature_count": len(Model.features),
                "native_name_record_count": len(Model.names),
                "native_scalar_count": len(Model.scalars),
                "stream_names": tuple((Record.name for Record in Archive.records)),
                "assembly_definition_count": len(Definitions),
                "assembly_instance_count": len(Instances),
                "assembly_flattened_occurrence_count": len(PathRecords),
                "assembly_mate_count": len(Mates),
                "assembly_flattened_mate_count": len(FlatMateValues),
                "assembly_mesh_count": len(Meshes),
            }
        ),
        units=UnitSystem.MILLIMETER,
        assembly=AsmValue,
    )
    DocValue.assert_valid()
    return DocValue


# this definition exists because focused behavior needs one stable owner
def ComponentFile(
    Label: str, Settings: ReadOptions
) -> dict[str, tuple[PathValue, ...]]:
    RequestedRoot = Settings.values.get("component_search_root")
    if RequestedRoot:
        RootValue = PathValue(str(RequestedRoot)).expanduser().resolve()
    else:
        Source = PathValue(Label)
        if not Source.is_file():
            return {}
        RootValue = Source.resolve().parent
    if not RootValue.is_dir():
        return {}
    Result: Defaultdict[str, list[PathValue]] = Defaultdict(list)
    for FilePath in RootValue.rglob("*"):
        if FilePath.is_file() and FilePath.suffix.casefold() in FormatIdBySuffix:
            Result[FilePath.name.casefold()].append(FilePath.resolve())

    # this callback exists because local behavior needs one focused transformation
    return {
        NameValue: tuple(sorted(Paths, key=lambda PathValue: str(PathValue).casefold()))
        for NameValue, Paths in Result.items()
    }


# this definition exists because focused behavior needs one stable owner
def ResolvedPath(
    SourcePath: str, Index: dict[str, tuple[Path, ...]]
) -> PathValue | None:
    Native = PureWindowsPath(SourcePath)
    Candidates = Index.get(Native.name.casefold(), ())
    if not Candidates:
        return None
    NativeParts = tuple((PartValue.casefold() for PartValue in Native.parts))

    # this definition exists because focused behavior needs one stable owner
    def Score(Choice: Path) -> tuple[int, str]:
        ChoiceParts = tuple((PartValue.casefold() for PartValue in Choice.parts))
        Matches = 0
        for LeftValue, Right in zip(reversed(NativeParts), reversed(ChoiceParts)):
            if LeftValue != Right:
                break
            Matches += 1
        return (Matches, str(Choice).casefold())

    return max(Candidates, key=Score)


# this definition exists because assembly source discovery must retain diagnostics
def FindAsmSources(Native: NativeAssembly, Index: dict[str, tuple[Path, ...]]) -> tuple[
    dict[PathValue, list[NativeAsmDefinition]],
    dict[int, PathValue],
    list[DiagValue],
]:
    RootId = Native.root_definition_id
    DefinitionsByPath: Defaultdict[PathValue, list[NativeAsmDefinition]] = Defaultdict(
        list
    )
    ResolvedPaths: dict[int, PathValue] = {}
    Diagnostics: list[DiagValue] = []
    for Definition in Native.definitions:
        if Definition.object_id == RootId:
            continue
        Resolved = ResolvedPath(Definition.source_path, Index)
        if Resolved is None:
            Diagnostics.append(
                DiagValue(
                    code="sldasm.component_source_missing",
                    message=f"component source is unavailable: {Definition.source_path}",
                    severity=Severity.INFO,
                    attributes=FrozenMapping(
                        {
                            "native_definition_id": Definition.object_id,
                            "configuration": Definition.configuration_name,
                        }
                    ),
                )
            )
            continue
        ResolvedPaths[Definition.object_id] = Resolved
        DefinitionsByPath[Resolved].append(Definition)
    return (dict(DefinitionsByPath), ResolvedPaths, Diagnostics)


# this definition exists because focused behavior needs one stable owner
def AsmDocuments(
    Adapter: SldprtAdapter,
    Native: NativeAssembly,
    Index: dict[str, tuple[Path, ...]],
    Settings: ReadOptions,
) -> tuple[
    tuple[ComponentDoc, ...],
    dict[int, str],
    dict[int, PathValue],
    tuple[DiagValue, ...],
]:
    if not Index:
        return ((), {}, {}, ())
    DefinitionsByPath, ResolvedPaths, Diagnostics = FindAsmSources(Native, Index)
    Documents: list[ComponentDoc] = []
    DocIds: dict[int, str] = {}

    # this callback exists because local behavior needs one focused transformation
    for Resolved, Definitions in sorted(
        DefinitionsByPath.items(), key=lambda ItemValue: str(ItemValue[0]).casefold()
    ):
        Representative = Definitions[0]
        Values = dict(Settings.values)
        Values["resolve_components"] = False
        Values["discover_companions"] = False
        Options = ReadOptions(
            configuration=Representative.configuration_name or None,
            include_brep=Settings.include_brep,
            include_tessellation=Representative.document_type == "ASSEMBLY",
            strict=Settings.strict,
            values=FrozenMapping(Values),
        )
        try:
            DocValue = Adapter.read(Resolved, Options)
        except (OSError, SldprtFormatError, TypeError, ValueError) as ErrorInfo:
            if Settings.strict:
                raise
            Diagnostics.append(
                DiagValue(
                    code="sldasm.component_decode_failed",
                    message=f"cannot decode {Resolved}: {ErrorInfo}",
                    severity=Severity.WARNING,
                    attributes=FrozenMapping(
                        {
                            "native_definition_ids": tuple(
                                (Definition.object_id for Definition in Definitions)
                            )
                        }
                    ),
                )
            )
            continue
        DocId = f"sldasm:document:{DocValue.source.sha256[:20]}"
        Documents.append(ComponentDoc(DocId, DocValue))
        for Definition in Definitions:
            DocIds[Definition.object_id] = DocId
    return (tuple(Documents), DocIds, ResolvedPaths, tuple(Diagnostics))


# this definition exists because component faces share one indexed mesh accumulator
def MeshGeometry(
    Component: NativeDisplay,
) -> tuple[
    list[VectorThree],
    list[VectorThree],
    list[tuple[int, int, int]],
    list[dict[str, object]],
]:
    Vertices: list[VectorThree] = []
    Normals: list[VectorThree] = []
    Triangles: list[tuple[int, int, int]] = []
    Faces: list[dict[str, object]] = []
    for FaceValue in Component.faces:
        VertexStart = len(Vertices)
        TriangleStart = len(Triangles)
        Vertices.extend((VectorThree(*Point) for Point in FaceValue.positions_mm))
        Normals.extend((VectorThree(*Normal) for Normal in FaceValue.normals))
        Triangles.extend(
            (
                (
                    Triangle[0] + VertexStart,
                    Triangle[1] + VertexStart,
                    Triangle[2] + VertexStart,
                )
                for Triangle in FaceValue.triangle_indices
            )
        )
        Faces.append(
            {
                "face_id": FaceValue.face_id,
                "vertex_start": VertexStart,
                "vertex_count": len(FaceValue.positions_mm),
                "triangle_start": TriangleStart,
                "triangle_count": len(FaceValue.triangle_indices),
                "strip_lengths": FaceValue.strip_lengths,
                "source_offset": FaceValue.offset,
                "source_length": FaceValue.record_length,
            }
        )
    return (Vertices, Normals, Triangles, Faces)


# this definition exists because focused behavior needs one stable owner
def AsmMeshes(Native: NativeAssembly) -> tuple[tuple[MeshValue, ...], dict[int, str]]:
    DefinitionByPath = {
        ItemValue.path.casefold(): ItemValue.definition_id
        for ItemValue in Native.occurrence_paths
    }
    ItemById = {ItemValue.object_id: ItemValue for ItemValue in Native.occurrences}
    Identity = {ObjectId: ObjectId for ObjectId in ItemById}
    DefinitionById = {
        Definition.object_id: Definition for Definition in Native.definitions
    }
    Result: list[MeshValue] = []
    MeshIds: dict[int, str] = {}
    for Component in Native.display_components:
        DefinitionId = DefinitionByPath.get(Component.occurrence_path.casefold())
        if DefinitionId is None:
            try:
                PathValue = MateInstance(Native, Identity, Component.occurrence_path)
            except SldprtFormatError:
                PathValue = ()
            if PathValue:
                DefinitionId = ItemById[PathValue[-1]].definition_id
        if DefinitionId is None or DefinitionId in MeshIds:
            continue
        Vertices, Normals, Triangles, Faces = MeshGeometry(Component)
        Definition = DefinitionById[DefinitionId]
        MeshId = f"sldasm:mesh:{DefinitionId}"
        Result.append(
            MeshValue(
                id=MeshId,
                name=f"{Definition.name} tessellation",
                vertices=tuple(Vertices),
                triangles=tuple(Triangles),
                normals=tuple(Normals),
                provenance=Provenance(
                    adapter=KAsmFormatId,
                    native_id=str(DefinitionId),
                    spans=(
                        ProvenanceSpan(
                            DisplayListsStream,
                            Component.record_offset,
                            Component.record_length,
                            "component-tessellation",
                        ),
                    ),
                ),
                attributes=FrozenMapping(
                    {
                        "occurrence_path": Component.occurrence_path,
                        "source_path": Component.source_path,
                        "faces": tuple(Faces),
                    }
                ),
            )
        )
        MeshIds[DefinitionId] = MeshId
    return (tuple(Result), MeshIds)


# this definition exists because focused behavior needs one stable owner
def AsmDefinitions(
    Native: NativeAssembly,
    DocIds: dict[int, str],
    ResolvedPaths: dict[int, Path],
    Documents: dict[str, CadDocument],
    MeshIds: dict[int, str],
    Label: str,
) -> tuple[ComponentDefinition, ...]:
    Result: list[ComponentDefinition] = []
    for Definition in Native.definitions:
        DocId = DocIds.get(Definition.object_id, "")
        DocValue = Documents.get(DocId)
        SourcePath = ResolvedPaths.get(Definition.object_id)
        if (
            Definition.object_id == Native.root_definition_id
            and PathValue(Label).is_file()
        ):
            SourcePath = PathValue(Label).resolve()
        KindValue = (
            ComponentKind.ASSEMBLY
            if Definition.document_type == "ASSEMBLY"
            else (
                ComponentKind.PART
                if Definition.document_type == "PART"
                else ComponentKind.NATIVE
            )
        )
        Result.append(
            ComponentDefinition(
                id=AsmDefinitionId(Definition.object_id),
                name=Definition.name,
                kind=KindValue,
                document_id=DocId,
                configuration_name=Definition.configuration_name,
                configuration_id=str(Definition.configuration_id),
                bounding_box=AsmBoundingBox(Definition.bounding_box_m),
                body_ids=(
                    tuple((BodyValue.id for BodyValue in DocValue.bodies))
                    if DocValue is not None and KindValue == ComponentKind.PART
                    else ()
                ),
                mesh_ids=(
                    (MeshIds[Definition.object_id],)
                    if Definition.object_id in MeshIds
                    else ()
                ),
                source_path=(
                    str(SourcePath)
                    if SourcePath is not None
                    else Definition.source_path
                ),
                source_format_id=(
                    KAsmFormatId if KindValue == ComponentKind.ASSEMBLY else KFormatId
                ),
                source_sha256=DocValue.source.sha256 if DocValue is not None else "",
                provenance=Provenance(
                    adapter=KAsmFormatId,
                    native_id=str(Definition.object_id),
                    spans=(
                        ProvenanceSpan(
                            ComponentTreeStream, 0, 0, "component-definition"
                        ),
                    ),
                ),
                attributes=FrozenMapping(
                    {
                        "native_object_id": Definition.object_id,
                        "native_file_id": Definition.file_id,
                        "native_source_path": Definition.source_path,
                        "alternate_configuration_name": Definition.alternate_configuration_name,
                        "last_modified_stamp": Definition.last_modified_stamp,
                        "configuration_flags": Definition.configuration_flags,
                        "child_occurrence_ids": Definition.child_occurrence_ids,
                        "native_attributes": Definition.attributes,
                    }
                ),
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def AsmInstances(Native: NativeAssembly) -> tuple[ComponentInstance, ...]:
    return tuple(
        (
            ComponentInstance(
                id=AsmInstanceId(ItemValue.object_id),
                name=f"{ItemValue.name}-{ItemValue.reference_number}",
                definition_id=AsmDefinitionId(ItemValue.definition_id),
                owner_definition_id=AsmDefinitionId(ItemValue.owner_definition_id),
                transform=AsmMatrix(ItemValue.transform),
                order=ItemValue.order,
                reference_number=str(ItemValue.reference_number),
                configuration_name=ItemValue.configuration_name,
                configuration_id=str(ItemValue.configuration_id),
                suppressed=ItemValue.suppressed,
                hidden=ItemValue.hidden,
                fixed=False,
                flexible=ItemValue.flexible,
                exclude_from_bom=ItemValue.exclude_from_bom,
                provenance=Provenance(
                    adapter=KAsmFormatId,
                    native_id=str(ItemValue.object_id),
                    spans=(
                        ProvenanceSpan(ComponentTreeStream, 0, 0, "component-instance"),
                    ),
                ),
                attributes=FrozenMapping(
                    {
                        "native_feature_id": ItemValue.feature_id,
                        "native_reference_number": ItemValue.reference_number,
                        "component_reference": ItemValue.component_reference,
                        "native_transform": ItemValue.transform,
                        "transform_stamp": ItemValue.transform_stamp,
                        "virtual": ItemValue.virtual,
                        "zone": ItemValue.zone,
                        "display_mode": ItemValue.display_mode,
                        "display_quality": ItemValue.display_quality,
                        "edges_in_shaded_mode": ItemValue.edges_in_shaded_mode,
                        "native_attributes": ItemValue.attributes,
                    }
                ),
            )
            for ItemValue in Native.occurrences
        )
    )


# this definition exists because focused behavior needs one stable owner
def MateSources(
    RootValue: NativeAssembly,
    Archive: SldprtArchive,
    Label: str,
    Index: dict[str, tuple[Path, ...]],
    Settings: ReadOptions,
) -> tuple[
    tuple[tuple[NativeAsm, SldprtArchive, dict[int, int], dict[int, int], str], ...],
    tuple[DiagValue, ...],
]:
    Sources = [
        (
            RootValue,
            Archive,
            {
                Definition.object_id: Definition.object_id
                for Definition in RootValue.definitions
            },
            {
                ItemValue.object_id: ItemValue.object_id
                for ItemValue in RootValue.occurrences
            },
            Label,
        )
    ]
    Diagnostics: list[DiagValue] = []
    for Target in RootValue.definitions:
        if (
            Target.document_type != "ASSEMBLY"
            or Target.object_id == RootValue.root_definition_id
        ):
            continue
        Resolved = ResolvedPath(Target.source_path, Index)
        if Resolved is None:
            Message = (
                f"nested assembly mate source is unavailable: {Target.source_path}"
            )
            if Settings.strict:
                raise SldprtFormatError(Message)
            Diagnostics.append(
                DiagValue(
                    code="sldasm.nested_mates_missing",
                    message=Message,
                    severity=Severity.WARNING,
                )
            )
            continue
        NestedArchive = SldprtArchive.open(Resolved)
        Nested = DecodeNativeAsm(NestedArchive, include_tessellation=False)
        try:
            DefinitionMap = NestedMap(RootValue, Nested, Target.object_id)
            ItemMap = NestedItemMap(RootValue, Nested, DefinitionMap)
        except SldprtFormatError as ErrorInfo:
            if Settings.strict:
                raise
            Diagnostics.append(
                DiagValue(
                    code="sldasm.nested_mates_unmapped",
                    message=f"cannot map nested mates from {Resolved}: {ErrorInfo}",
                    severity=Severity.WARNING,
                )
            )
            continue
        Sources.append((Nested, NestedArchive, DefinitionMap, ItemMap, str(Resolved)))
    return (tuple(Sources), tuple(Diagnostics))


# this definition exists because focused behavior needs one stable owner
def NativeKey(Definition: NativeAssemblyDefinition) -> tuple[str, str, str]:
    return (
        PureWindowsPath(Definition.source_path).name.casefold(),
        Definition.configuration_name.casefold(),
        Definition.document_type.casefold(),
    )


# this definition exists because focused behavior needs one stable owner
def NestedMap(
    RootValue: NativeAssembly, Nested: NativeAssembly, TargetRootId: int
) -> dict[int, int]:
    Result = {Nested.root_definition_id: TargetRootId}
    Targets: Defaultdict[tuple[str, str, str], list[NativeAsmDefinition]] = Defaultdict(
        list
    )
    for Definition in RootValue.definitions:
        Targets[NativeKey(Definition)].append(Definition)
    for Definition in Nested.definitions:
        if Definition.object_id == Nested.root_definition_id:
            continue
        Candidates = Targets.get(NativeKey(Definition), [])
        if len(Candidates) != 1:
            raise SldprtFormatError(
                f"nested definition {Definition.name!r} has {len(Candidates)} root mappings"
            )
        Result[Definition.object_id] = Candidates[0].object_id
    return Result


# this definition exists because focused behavior needs one stable owner
def NestedItemMap(
    RootValue: NativeAssembly, Nested: NativeAssembly, DefinitionMap: dict[int, int]
) -> dict[int, int]:
    Result: dict[int, int] = {}
    for ItemValue in Nested.occurrences:
        OwnerId = DefinitionMap[ItemValue.owner_definition_id]
        DefinitionId = DefinitionMap[ItemValue.definition_id]
        Candidates = tuple(
            (
                Target
                for Target in RootValue.occurrences
                if Target.owner_definition_id == OwnerId
                and Target.definition_id == DefinitionId
                and (Target.name.casefold() == ItemValue.name.casefold())
                and (Target.reference_number == ItemValue.reference_number)
                and (Target.feature_id == ItemValue.feature_id)
            )
        )
        if len(Candidates) != 1:
            raise SldprtFormatError(
                f"nested occurrence {ItemValue.name}-{ItemValue.reference_number} has {len(Candidates)} root mappings"
            )
        Result[ItemValue.object_id] = Candidates[0].object_id
    return Result


# this definition exists because focused behavior needs one stable owner
def AsmMates(
    RootValue: NativeAssembly,
    Sources: tuple[
        tuple[NativeAssembly, SldprtArchive, dict[int, int], dict[int, int], str], ...
    ],
) -> tuple[
    tuple[BrepPayload, ...],
    tuple[MateEntity, ...],
    tuple[MateRule, ...],
    tuple[MateGroup, ...],
]:
    Payloads: list[BrepPayload] = []
    Entities: list[MateEntity] = []
    Mates: list[MateRule] = []
    Groups: list[MateGroup] = []
    for SourceIndex, (
        Source,
        Archive,
        DefinitionMap,
        ItemMap,
        SourceLabel,
    ) in enumerate(Sources):
        for ListIndex, MateList in enumerate(Source.mate_lists):
            OwnerId = DefinitionMap[MateList.owner_definition_id]
            StreamData = Archive.require(MateList.stream)
            StreamName = (
                MateList.stream
                if SourceIndex == 0
                else f"{SourceLabel}::{MateList.stream}"
            )
            PayloadId = f"sldasm:mates:{OwnerId}:{ListIndex}"
            Payloads.append(
                MatePayload(
                    PayloadId, StreamName, StreamData, MateList, OwnerId, SourceLabel
                )
            )
            MateIdsByOrder: dict[int, str] = {}
            for MateValue in MateList.mates:
                if MateValue.kind == "group":
                    continue
                MateId = f"sldasm:mate:{OwnerId}:{ListIndex}:{MateValue.order}"
                EntityIds: list[str] = []
                for EntityIndex, NativeEntity in enumerate(MateValue.entities):
                    EntityId = f"{MateId}:entity:{EntityIndex}"
                    EntityIds.append(EntityId)
                    Entities.append(
                        AsmMateEntity(
                            EntityId,
                            OwnerId,
                            Source,
                            ItemMap,
                            NativeEntity,
                            MateValue,
                            StreamName,
                            SourceLabel,
                        )
                    )
                Mates.append(
                    MateRule(
                        id=MateId,
                        name=MateValue.name,
                        kind=NeutralMateKinA(MateValue.kind),
                        owner_definition_id=AsmDefinitionId(OwnerId),
                        entity_ids=tuple(EntityIds),
                        order=MateValue.order,
                        value=NeutralMateA(MateValue),
                        alignment=NeutralMate(MateValue),
                        suppressed=False,
                        driving=True,
                        provenance=MateProvenance(MateValue, StreamName),
                        attributes=FrozenMapping(
                            {
                                "native_kind": MateValue.kind,
                                "native_class_name": MateValue.class_name,
                                "native_class_token": MateValue.class_token,
                                "native_owner_definition_id": MateValue.owner_definition_id,
                                "native_record_offset": MateValue.record_offset,
                                "native_record_length": MateValue.record_length,
                                "native_payload_id": PayloadId,
                                "serialized_strings": MateValue.serialized_strings,
                                "source_document": SourceLabel,
                                "native_alignment_code": MateValue.alignment_code,
                                "native_dimensions": tuple(
                                    (
                                        {
                                            "name": Dimension.name,
                                            "value": Dimension.value,
                                            "value_offset": Dimension.value_offset,
                                        }
                                        for Dimension in MateValue.dimensions
                                    )
                                ),
                                "native_value_m": MateValue.value_m,
                                "native_value_offset": MateValue.value_offset,
                            }
                        ),
                    )
                )
                MateIdsByOrder[MateValue.order] = MateId
            Groups.extend(
                MateGroups(MateList, OwnerId, MateIdsByOrder, StreamName, PayloadId)
            )
    return (tuple(Payloads), tuple(Entities), tuple(Mates), tuple(Groups))


# this definition exists because focused behavior needs one stable owner
def MatePayload(
    PayloadId: str,
    StreamName: str,
    DataValue: bytes,
    MateList: NativeMateList,
    OwnerId: int,
    SourceLabel: str,
) -> BrepPayload:
    return BrepPayload(
        id=PayloadId,
        format_id="solidworks.mates",
        kind="mate-list",
        schema="solidworks.serialized-object-stream",
        sha256=Hashlib.sha256(DataValue).hexdigest(),
        data=DataValue,
        source_stream=StreamName,
        provenance=Provenance(
            adapter=KAsmFormatId,
            native_id=str(MateList.native_id),
            spans=(ProvenanceSpan(StreamName, 0, len(DataValue), "mate-list"),),
        ),
        attributes=FrozenMapping(
            {
                "native_id": MateList.native_id,
                "declared_count": MateList.declared_count,
                "owner_definition_id": OwnerId,
                "source_document": SourceLabel,
                "records": tuple(
                    (
                        {
                            "name": MateValue.name,
                            "kind": MateValue.kind,
                            "class_name": MateValue.class_name,
                            "class_token": MateValue.class_token,
                            "offset": MateValue.record_offset,
                            "length": MateValue.record_length,
                        }
                        for MateValue in MateList.mates
                    )
                ),
            }
        ),
        role=PayloadRole.ASSEMBLY_STRUCTURE,
        file_extension=".bin",
    )


# this definition exists because focused behavior needs one stable owner
def AsmMateEntity(
    EntityId: str,
    OwnerId: int,
    Source: NativeAssembly,
    ItemMap: dict[int, int],
    Entity: NativeMateEntity,
    MateValue: NativeMate,
    StreamName: str,
    SourceLabel: str,
) -> MateEntity:
    PathValue = MateInstance(Source, ItemMap, Entity.component_path)
    SourceEntityId = (
        Entity.persistent_references[-1] if Entity.persistent_references else ""
    )
    return MateEntity(
        id=EntityId,
        owner_definition_id=AsmDefinitionId(OwnerId),
        instance_path=tuple((AsmInstanceId(Value) for Value in PathValue)),
        kind=NeutralMateKind(SourceEntityId),
        source_entity_id=SourceEntityId,
        provenance=MateProvenance(MateValue, StreamName),
        attributes=FrozenMapping(
            {
                "component_path": Entity.component_path,
                "persistent_references": Entity.persistent_references,
                "source_path": Entity.source_path,
                "configuration_name": Entity.configuration_name,
                "source_document": SourceLabel,
            }
        ),
    )


# this definition exists because focused behavior needs one stable owner
def MateInstance(
    Source: NativeAssembly, ItemMap: dict[int, int], ComponentPath: str
) -> tuple[int, ...]:
    if not ComponentPath:
        return ()
    Children: Defaultdict[int, list[NativeAsmItem]] = Defaultdict(list)
    for ItemValue in Source.occurrences:
        Children[ItemValue.owner_definition_id].append(ItemValue)
    OwnerId = Source.root_definition_id
    Result: list[int] = []
    for RawSegment in ComponentPath.split("/"):
        Segment = RawSegment.split("@", 1)[0].strip().casefold()
        Candidates = tuple(
            (
                ItemValue
                for ItemValue in Children.get(OwnerId, [])
                if Segment
                in {
                    ItemValue.name.strip().casefold(),
                    f"{ItemValue.name}-{ItemValue.reference_number}".strip().casefold(),
                }
            )
        )
        if not Candidates:
            return ()
        if len(Candidates) != 1:
            raise SldprtFormatError(
                f"mate component path segment {RawSegment!r} has {len(Candidates)} hierarchy mappings"
            )
        ItemValue = Candidates[0]
        Mapped = ItemMap.get(ItemValue.object_id)
        if Mapped is None:
            raise SldprtFormatError(
                f"mate component path references unmapped occurrence {ItemValue.object_id}"
            )
        Result.append(Mapped)
        OwnerId = ItemValue.definition_id
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def NeutralMateKinA(Value: str) -> MateKind:
    Alias = NativeMateNeutralKind.get(Value)
    if Alias is not None:
        return MateKind(Alias)
    try:
        return MateKind(Value)
    except ValueError:
        return MateKind.NATIVE


# this definition exists because focused behavior needs one stable owner
def NeutralMate(MateValue: NativeMate) -> MateAlignment:
    AlignmentCode = MateValue.alignment_code
    if AlignmentCode is None:
        return MateAlignment.UNKNOWN
    Alignment = NativeMateAlignmentByCode.get(AlignmentCode)
    if Alignment is None:
        return MateAlignment.UNKNOWN
    return MateAlignment(Alignment.kind)


# this definition exists because focused behavior needs one stable owner
def NeutralMateA(MateValue: NativeMate) -> ParamValue | None:
    Dimensions = MateValue.dimensions
    if not Dimensions:
        return None
    Semantic = MateValueSemantics.get(MateValue.kind)
    if Semantic == "angle":
        return ParamValue(Dimensions[0].value, ValueKind.ANGLE, "rad")
    if Semantic == "length":
        return ParamValue(Dimensions[0].value * 1000.0, ValueKind.LENGTH, "mm")
    if Semantic == "ratio" and len(Dimensions) >= 2:
        Denominator = Dimensions[1].value
        if Denominator != 0.0:
            return ParamValue(Dimensions[0].value / Denominator, ValueKind.NUMBER, "")
    return None


# this definition exists because focused behavior needs one stable owner
def NeutralMateKind(Value: str) -> MateEntityKind:
    Lowered = Value.casefold()
    for Marker, KindValue in NativeMateEntityMarkers:
        if Marker in Lowered:
            return MateEntityKind(KindValue)
    return MateEntityKind.NATIVE


# this definition exists because focused behavior needs one stable owner
def MateProvenance(MateValue: NativeMate, StreamName: str) -> Provenance:
    return Provenance(
        adapter=KAsmFormatId,
        native_id=MateValue.name,
        spans=(
            ProvenanceSpan(
                StreamName,
                MateValue.record_offset,
                MateValue.record_length,
                "mate-record",
            ),
        ),
    )


# this definition exists because focused behavior needs one stable owner
def MateGroups(
    MateList: NativeMateList,
    OwnerId: int,
    MateIdsByOrder: dict[int, str],
    StreamName: str,
    PayloadId: str,
) -> tuple[MateGroup, ...]:
    Result: list[MateGroup] = []
    Records = MateList.mates
    Markers = tuple((Record for Record in Records if Record.kind == "group"))
    for PairIndex in range(0, len(Markers) - 1, 2):
        Marker = Markers[PairIndex]
        EndValue = Markers[PairIndex + 1]
        NextStart = (
            Markers[PairIndex + 2].order
            if PairIndex + 2 < len(Markers)
            else len(Records)
        )
        Members: list[str] = []
        for Choice in Records:
            if (
                Choice.order <= EndValue.order
                or Choice.order >= NextStart
                or Choice.kind == "group"
            ):
                continue
            MateId = MateIdsByOrder.get(Choice.order)
            if MateId is not None:
                Members.append(MateId)
            if Choice.kind == "lock_to_sketch":
                break
        Result.append(
            MateGroup(
                id=f"sldasm:mate-group:{OwnerId}:{Marker.order}",
                name=Marker.name,
                owner_definition_id=AsmDefinitionId(OwnerId),
                mate_ids=tuple(Members),
                order=Marker.order,
                provenance=Provenance(
                    adapter=KAsmFormatId,
                    native_id=Marker.name,
                    spans=(
                        ProvenanceSpan(
                            StreamName,
                            Marker.record_offset,
                            Marker.record_length,
                            "mate-group-start",
                        ),
                        ProvenanceSpan(
                            StreamName,
                            EndValue.record_offset,
                            EndValue.record_length,
                            "mate-group-end",
                        ),
                    ),
                ),
                attributes=FrozenMapping(
                    {
                        "native_payload_id": PayloadId,
                        "start_record_offset": Marker.record_offset,
                        "start_record_length": Marker.record_length,
                        "end_record_offset": EndValue.record_offset,
                        "end_record_length": EndValue.record_length,
                    }
                ),
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def Flattened(Native: NativeAssembly) -> tuple[dict[str, object], ...]:
    Identity = {
        ItemValue.object_id: ItemValue.object_id for ItemValue in Native.occurrences
    }
    return tuple(
        (
            {
                "occurrence_id": AsmInstanceId(ItemValue.occurrence_id),
                "definition_id": AsmDefinitionId(ItemValue.definition_id),
                "path": ItemValue.path,
                "instance_path": tuple(
                    (
                        AsmInstanceId(Value)
                        for Value in MateInstance(Native, Identity, ItemValue.path)
                    )
                ),
                "depth": ItemValue.depth,
            }
            for ItemValue in Native.occurrence_paths
        )
    )


# this definition exists because focused behavior needs one stable owner
def FlattenedMates(
    Native: NativeAssembly, Mates: tuple[MateConstraint, ...]
) -> tuple[dict[str, object], ...]:
    Identity = {
        ItemValue.object_id: ItemValue.object_id for ItemValue in Native.occurrences
    }
    OwnerPaths: Defaultdict[int, list[tuple[str, tuple[str, ...]]]] = Defaultdict(list)
    OwnerPaths[Native.root_definition_id].append(("", ()))
    for ItemValue in Native.occurrence_paths:
        InstanceIds = tuple(
            (
                AsmInstanceId(Value)
                for Value in MateInstance(Native, Identity, ItemValue.path)
            )
        )
        OwnerPaths[ItemValue.definition_id].append((ItemValue.path, InstanceIds))
    Result: list[dict[str, object]] = []
    for MateValue in Mates:
        OwnerId = int(MateValue.owner_definition_id.rsplit(":", 1)[-1])
        for Index, (SourcePath, InstancePath) in enumerate(OwnerPaths.get(OwnerId, [])):
            Result.append(
                {
                    "id": f"{MateValue.id}:occurrence:{Index}",
                    "mate_id": MateValue.id,
                    "owner_definition_id": MateValue.owner_definition_id,
                    "owner_occurrence_path": SourcePath,
                    "owner_instance_path": InstancePath,
                }
            )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def Companion(Label: str) -> tuple[BrepPayload, ...]:
    Source = PathValue(Label)
    if not Source.is_file():
        return ()
    Source = Source.resolve()
    Specifications = (
        ("ACIS", ".sat", "acis.sat"),
        ("Parasolid", ".x_t", "parasolid.x_t"),
    )
    Result: list[BrepPayload] = []
    for FolderName, Suffix, FormatId in Specifications:
        Folder = Source.parent / FolderName
        if not Folder.is_dir():
            continue
        Choice = next(
            (
                PathValue
                for PathValue in Folder.iterdir()
                if PathValue.is_file()
                and PathValue.stem.casefold() == Source.stem.casefold()
                and (PathValue.suffix.casefold() == Suffix)
            ),
            None,
        )
        if Choice is None:
            continue
        DataValue = Choice.read_bytes()
        Attributes: dict[str, object] = {
            "companion_path": str(Choice.resolve()),
            "source_assembly": str(Source),
        }
        if FormatId == "acis.sat":
            Header = DataValue.splitlines()[0].decode("ascii", errors="replace").split()
            if len(Header) >= 3 and Header[2].isdigit():
                Attributes["body_count"] = int(Header[2])
        Result.append(
            BrepPayload(
                id=f"sldasm:resolved:{FormatId}",
                format_id=FormatId,
                kind="resolved-assembly",
                schema=FormatId,
                sha256=Hashlib.sha256(DataValue).hexdigest(),
                data=DataValue,
                source_stream=str(Choice.resolve()),
                provenance=Provenance(
                    adapter=KAsmFormatId,
                    native_id=Choice.name,
                    spans=(
                        ProvenanceSpan(
                            str(Choice.resolve()),
                            0,
                            len(DataValue),
                            "resolved-assembly-brep",
                        ),
                    ),
                ),
                attributes=FrozenMapping(Attributes),
                role=PayloadRole.BREP,
                file_extension=Suffix,
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def AsmMatrix(Values: tuple[float, ...]) -> MatrixFour:
    return MatrixFour(
        (
            Values[0],
            Values[4],
            Values[8],
            Values[12] * 1000.0,
            Values[1],
            Values[5],
            Values[9],
            Values[13] * 1000.0,
            Values[2],
            Values[6],
            Values[10],
            Values[14] * 1000.0,
            Values[3],
            Values[7],
            Values[11],
            Values[15],
        )
    )


# this definition exists because focused behavior needs one stable owner
def AsmBoundingBox(
    Values: tuple[float, float, float, float, float, float] | None,
) -> BoundingBox | None:
    if Values is None:
        return None
    return BoundingBox(
        VectorThree(*(Value * 1000.0 for Value in Values[:3])),
        VectorThree(*(Value * 1000.0 for Value in Values[3:])),
    )


# this definition exists because focused behavior needs one stable owner
def AsmDefinitionId(NativeId: int) -> str:
    return f"sldasm:definition:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def AsmInstanceId(NativeId: int) -> str:
    return f"sldasm:instance:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def ValidateSource(Label: str, IsAsm: bool) -> None:
    Suffix = PathValue(Label).suffix.casefold()
    ExpectedFormat = KAsmFormatId if IsAsm else KFormatId
    Expected = SuffixByFormatId[ExpectedFormat]
    if Suffix in FormatIdBySuffix and Suffix != Expected:
        KindValue = "assembly" if IsAsm else "part"
        raise SldprtFormatError(
            f"SOLIDWORKS {KindValue} content requires a {Expected.upper()} source"
        )


# stream restoration remains best effort for nonseekable and closed inputs
def RestoreStream(SourceData: Source, Position: int | None) -> None:
    SeekValue = getattr(SourceData, "seek", None)
    if Position is None or not callable(SeekValue):
        return
    try:
        _ = SeekValue(Position)
    except (OSError, ValueError):
        return


# this definition exists because focused behavior needs one stable owner
def SourceBytes(Source: Source) -> tuple[bytes, str]:
    if isinstance(Source, (str, FilePath)):
        LocalPath = FilePath(Source).expanduser().resolve()
        return (LocalPath.read_bytes(), str(LocalPath))
    if isinstance(Source, (bytes, bytearray)):
        return (bytes(Source), "<memory>")
    Position = None
    TellValue = getattr(Source, "tell", None)
    if callable(TellValue):
        try:
            PositionValue = TellValue()
            Position = PositionValue if isinstance(PositionValue, int) else None
        except (OSError, ValueError):
            Position = None
    Value = Source.read()
    RestoreStream(Source, Position)
    if not isinstance(Value, (bytes, bytearray)):
        raise TypeError("SLDPRT source stream must yield bytes")
    NameValue = getattr(Source, "name", "<stream>")
    return (bytes(Value), str(NameValue))


# this definition exists because focused behavior needs one stable owner
def ResolvedStream(Streams: Mapping[str, bytes], LaneValue: str) -> str:
    return KitResolvedStream if KitResolvedStream in Streams else LaneValue


# this definition exists because focused behavior needs one stable owner
def NativePartModel(Archive: SldprtArchive, Requested: str | None) -> NativeModel:
    Keywords = Archive.require(KeywordsStream)
    Lanes = {
        int(Match.group(1)): NameValue
        for NameValue in Archive.streams
        if (Match := KResolvedConfigStream.fullmatch(NameValue)) is not None
    }
    if not Lanes:
        raise SldprtFormatError("required native resolved-feature stream is missing")
    InitialId = 0 if 0 in Lanes else min(Lanes)
    InitialStream = ResolvedStream(Archive.streams, Lanes[InitialId])
    Initial = DecodeNativeModel(
        Keywords,
        Archive.require(InitialStream),
        configuration_id=InitialId,
        resolved_stream=InitialStream,
    )
    SelectedId = InitialId
    if Requested is not None:
        Selected = next(
            (
                ItemValue.configuration_id
                for ItemValue in Initial.configurations
                if ItemValue.name == Requested
            ),
            None,
        )
        if Selected is None:
            raise SldprtFormatError(
                f"configuration {Requested!r} is unavailable; choices are {sorted((ItemValue.name for ItemValue in Initial.configurations))}"
            )
        SelectedId = Selected
    if SelectedId not in Lanes:
        raise SldprtFormatError(
            f"native data for configuration {SelectedId} is unavailable; available lanes are {sorted(Lanes)}"
        )
    SelectedStream = ResolvedStream(Archive.streams, Lanes[SelectedId])
    ConfigStream = f"Contents/Config-{SelectedId}"
    return DecodeNativeModel(
        Keywords,
        Archive.require(SelectedStream),
        Archive.get(ConfigStream) or b"",
        configuration_id=SelectedId,
        resolved_stream=SelectedStream,
        configuration_stream=ConfigStream,
    )


# this definition exists because focused behavior needs one stable owner
def Configurations(Model: NativeModel, Requested: str | None) -> tuple[Config, ...]:
    Available = {ItemValue.name for ItemValue in Model.configurations}
    if Requested is not None and Requested not in Available:
        raise SldprtFormatError(
            f"configuration {Requested!r} is unavailable; choices are {sorted(Available)}"
        )
    Active = Requested or next(
        (
            ItemValue.name
            for ItemValue in Model.configurations
            if ItemValue.configuration_id == Model.active_configuration_id
        ),
        Model.configurations[0].name,
    )
    return tuple(
        (
            Config(
                id=ConfigId(ItemValue.configuration_id),
                name=ItemValue.name,
                active=ItemValue.name == Active,
                attributes=FrozenMapping(
                    {
                        "native_object_id": ItemValue.object_id,
                        "native_configuration_id": ItemValue.configuration_id,
                        "native_properties": ItemValue.properties,
                    }
                ),
            )
            for ItemValue in Model.configurations
        )
    )


# this definition exists because focused behavior needs one stable owner
def Parameters(Model: NativeModel) -> tuple[Param, ...]:
    Parameters: list[Param] = []
    DimensionIds: dict[tuple[str, str], str] = {}
    for Feature in Model.features:
        for Dimension, ParamId in ParamEntries(Feature.object_id, Feature.dimensions):
            NativeValue = (
                Dimension.native_value
                if Dimension.native_value is not None
                else Dimension.value_mm / 1000.0
            )
            Parameters.append(
                Param(
                    id=ParamId,
                    name=Dimension.name,
                    value=DimensionParam(Dimension),
                    role=(
                        ParamRole.DRIVEN
                        if Dimension.native_role == "display"
                        else ParamRole.DRIVING
                    ),
                    owner_id=FeatureId(Feature.object_id),
                    provenance=(
                        ProvenanceA(
                            f"{Feature.object_id}:{Dimension.name}",
                            Dimension.native_offset,
                            8,
                            "dimension-scalar",
                            Stream=Feature.native_stream,
                        )
                        if Dimension.native_offset is not None
                        else FeatureA(Feature)
                    ),
                    attributes=FrozenMapping(
                        {
                            "source_text": Dimension.source_text,
                            "dimension_kind": Dimension.kind,
                            "native_value": NativeValue,
                            "native_unit": "rad" if Dimension.kind == "angle" else "m",
                            "native_role": Dimension.native_role or "unresolved",
                            "native_operands": tuple(
                                (
                                    {
                                        "offset": Operand.offset,
                                        "kind_code": Operand.kind_code,
                                        "entity_index": Operand.entity_index,
                                    }
                                    for Operand in Dimension.operands
                                )
                            ),
                        }
                    ),
                )
            )
            _ = DimensionIds.setdefault((Feature.name, Dimension.name), ParamId)
    return ApplyNativeMut(Parameters, Model, DimensionIds)


# this definition exists because focused behavior needs one stable owner
def DimensionParam(Dimension: NativeDimension) -> ParamValue:
    if Dimension.kind == "angle":
        return ParamValue(Dimension.value_mm, ValueKind.ANGLE, "deg")
    return ParamValue(Dimension.value_mm, ValueKind.LENGTH, "mm")


# this definition exists because focused behavior needs one stable owner
def ApplyNativeMut(
    Parameters: list[Parameter],
    Model: NativeModel,
    DimensionIds: dict[tuple[str, str], str],
) -> tuple[Param, ...]:
    if not Model.equations:
        return tuple(Parameters)
    GlobalIds = {
        Equation.lhs: f"sldprt:parameter:equation:{Equation.lhs}"
        for Equation in Model.equations
        if "@" not in Equation.lhs
    }
    Values: dict[str, ParamValue] = {}
    ParamIndexes = {Param.id: Index for Index, Param in enumerate(Parameters)}
    for Equation in Model.equations:
        RefIds = tuple(
            (
                GlobalIds[RefValue]
                for RefValue in Equation.references
                if RefValue in GlobalIds
            )
        )
        ExprValue = Expression(Equation.rhs, RefIds, "solidworks")
        ProvenanceValue = Provenance(
            adapter=KFormatId,
            native_id=f"equation:{Equation.native_offset}",
            spans=(
                ProvenanceSpan(
                    Equation.native_stream,
                    Equation.native_offset,
                    Equation.native_length,
                    "equation",
                ),
            ),
        )
        if "@" in Equation.lhs:
            DimensionName, FeatureName = Equation.lhs.split("@", 1)
            ParamId = DimensionIds.get((FeatureName, DimensionName))
            if ParamId is None or ParamId not in ParamIndexes:
                continue
            Index = ParamIndexes[ParamId]
            Parameters[Index] = Replace(
                Parameters[Index],
                role=ParamRole.DERIVED,
                expression=ExprValue,
                provenance=ProvenanceValue,
                attributes=FrozenMapping(
                    {
                        **dict(Parameters[Index].attributes),
                        "equation_source": Equation.source,
                        "equation_configuration_id": Equation.configuration_id,
                    }
                ),
            )
            continue
        Value = NativeEquation(Equation.rhs, Values)
        if Value is None:
            Value = ParamValue(Equation.rhs, ValueKind.STRING)
        Values[Equation.lhs] = Value
        ParamItem = Param(
            id=GlobalIds[Equation.lhs],
            name=Equation.lhs,
            value=Value,
            role=ParamRole.DERIVED if Equation.references else ParamRole.DRIVING,
            expression=ExprValue,
            owner_id=FeatureId(16),
            provenance=ProvenanceValue,
            attributes=FrozenMapping(
                {
                    "equation_source": Equation.source,
                    "equation_configuration_id": Equation.configuration_id,
                }
            ),
        )
        if ParamItem.id in ParamIndexes:
            Parameters[ParamIndexes[ParamItem.id]] = ParamItem
        else:
            ParamIndexes[ParamItem.id] = len(Parameters)
            Parameters.append(ParamItem)
    return tuple(Parameters)


# this definition exists because focused behavior needs one stable owner
def NativeEquation(
    RhsValue: str, Values: Mapping[str, ParameterValue]
) -> ParamValue | None:
    Literal = RegexLib.fullmatch(
        "\\s*([-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+))\\s*mm\\s*",
        RhsValue,
        RegexLib.IGNORECASE,
    )
    if Literal is not None:
        return ParamValue(float(Literal.group(1)), ValueKind.LENGTH, "mm")
    Number = RegexLib.fullmatch("\\s*([-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+))\\s*", RhsValue)
    if Number is not None:
        return ParamValue(float(Number.group(1)), ValueKind.NUMBER, "")
    Quotient = RegexLib.fullmatch(
        '\\s*"([^"\\r\\n]+)"\\s*/\\s*([-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+))\\s*', RhsValue
    )
    if Quotient is None:
        return None
    Source = Values.get(Quotient.group(1))
    if (
        Source is None
        or Source.kind not in {ValueKind.LENGTH, ValueKind.NUMBER}
        or (not isinstance(Source.value, (int, float)))
    ):
        return None
    Divisor = float(Quotient.group(2))
    if not MathValue.isfinite(Divisor) or Divisor == 0.0:
        return None
    return ParamValue(float(Source.value) / Divisor, Source.kind, Source.unit)


# this definition exists because focused behavior needs one stable owner
def Planes(Model: NativeModel, ParamIds: set[str]) -> tuple[SupportPlane, ...]:
    Result: list[SupportPlane] = []

    # this callback exists because local behavior needs one focused transformation
    for Plane in sorted(
        Model.planes,
        key=lambda ItemValue: (
            next(
                (
                    Feature.native_offset
                    for Feature in Model.features
                    if Feature.object_id == ItemValue.object_id
                ),
                None,
            )
            is None,
            next(
                (
                    Feature.native_offset
                    for Feature in Model.features
                    if Feature.object_id == ItemValue.object_id
                ),
                1 << 62,
            ),
        ),
    ):
        OffsetId = ParamId(Plane.object_id, "D1")
        Result.append(
            SupportPlane(
                id=PlaneId(Plane.object_id),
                name=Plane.name,
                transform=Transform(
                    origin=VectorThree(*Plane.origin_mm),
                    x_axis=VectorThree(*Plane.u_axis),
                    y_axis=VectorThree(*Plane.v_axis),
                    z_axis=VectorThree(*Plane.normal),
                ),
                offset_parameter_id=OffsetId if OffsetId in ParamIds else None,
                provenance=(
                    ProvenanceA(
                        str(Plane.object_id),
                        Plane.native_offset,
                        Plane.native_length or 1,
                        "support-plane-frame",
                        Stream=Plane.native_stream,
                    )
                    if Plane.native_offset is not None
                    else ProvenanceA(
                        str(Plane.object_id), None, None, "principal-plane"
                    )
                ),
                attributes=FrozenMapping(
                    {
                        "native_object_id": Plane.object_id,
                        "native_frame_offset": Plane.native_offset,
                        "native_frame_length": Plane.native_length,
                        "principal": Plane.principal,
                        "native_reference_ids": Plane.reference_ids,
                    }
                ),
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def Sketches(Model: NativeModel, ParamIds: set[str]) -> tuple[SketchData, ...]:

    # this callback exists because local behavior needs one focused transformation
    return tuple(
        (
            SketchA(Sketch, ParamIds)
            for Sketch in sorted(
                Model.sketches, key=lambda ItemValue: ItemValue.native_offset
            )
        )
    )


# this definition exists because profile primitives share one entity mapping pass
def ProfileSketch(
    Sketch: NativeSketch,
) -> tuple[list[SketchEntity], dict[str, str], dict[int, str], set[int]]:
    Entities: list[SketchEntity] = []
    RefMap: dict[str, str] = {}
    ProfileEntities: dict[int, str] = {}
    ProfileOffsets = {
        Offset for Profile in Sketch.profiles for Offset in Profile.marker_offsets
    }
    for ProfileIndex, Profile in enumerate(Sketch.profiles):
        if Profile.kind == "rectangle":
            XZero, YZero, XOneValue, YOneValue = Profile.coordinates
            Endpoints = (
                ((XZero, YZero), (XOneValue, YZero)),
                ((XOneValue, YZero), (XOneValue, YOneValue)),
                ((XOneValue, YOneValue), (XZero, YOneValue)),
                ((XZero, YOneValue), (XZero, YZero)),
            )
            for EdgeIndex, (Start, EndValue) in enumerate(Endpoints):
                EntityId = ProfileEdgeId(Sketch.object_id, ProfileIndex, EdgeIndex)
                MarkerOffset = (
                    Profile.marker_offsets[EdgeIndex]
                    if EdgeIndex < len(Profile.marker_offsets)
                    else None
                )
                Entities.append(
                    SketchEntity(
                        id=EntityId,
                        kind=GeomKind.LINE,
                        geometry=LineGeom(VectorTwo(*Start), VectorTwo(*EndValue)),
                        provenance=(
                            ProvenanceA(
                                f"{Sketch.object_id}:{MarkerOffset}",
                                MarkerOffset,
                                92,
                                "sketch-profile-line",
                                Stream=Sketch.native_stream,
                            )
                            if MarkerOffset is not None
                            else FeatureSpan(Sketch)
                        ),
                        attributes=FrozenMapping(
                            {"profile_index": ProfileIndex, "edge_index": EdgeIndex}
                        ),
                    )
                )
                RefMap[
                    f"{Sketch.object_id}:profile:{ProfileIndex}:edge:{EdgeIndex}"
                ] = EntityId
                if MarkerOffset is not None:
                    ProfileEntities[MarkerOffset] = EntityId
        elif Profile.kind == "circle":
            FirstCoord, SecondCoord, Radius = Profile.coordinates
            EntityId = ProfileId(Sketch.object_id, ProfileIndex)
            Entities.append(
                SketchEntity(
                    id=EntityId,
                    kind=GeomKind.CIRCLE,
                    geometry=CircleGeom(VectorTwo(FirstCoord, SecondCoord), Radius),
                    provenance=Provenance(
                        adapter=KFormatId,
                        native_id=f"{Sketch.object_id}:profile:{ProfileIndex}",
                        spans=tuple(
                            (
                                ProvenanceSpan(
                                    Sketch.native_stream,
                                    Offset,
                                    142,
                                    "sketch-circle-marker",
                                )
                                for Offset in Profile.marker_offsets
                            )
                        ),
                    ),
                    attributes=FrozenMapping({"profile_index": ProfileIndex}),
                )
            )
            RefMap[f"{Sketch.object_id}:profile:{ProfileIndex}"] = EntityId
            ProfileEntities.update(
                {Offset: EntityId for Offset in Profile.marker_offsets}
            )
    return (Entities, RefMap, ProfileEntities, ProfileOffsets)


# this definition exists because native markers share coordinate reference context
def SketchMarkers(
    Sketch: NativeSketch,
    ProfileOffsets: set[int],
    ProfileEntities: Mapping[int, str],
) -> tuple[list[SketchEntity], dict[int, str]]:
    Entities: list[SketchEntity] = []
    CoordinatesByPrefix = {
        Prefix: tuple(
            (
                Marker.coordinates_mm
                for Marker in Sketch.markers
                if Marker.prefix == Prefix
            )
        )
        for Prefix in {Marker.prefix for Marker in Sketch.markers}
    }
    CoordinatesByIndex = tuple((Marker.coordinates_mm for Marker in Sketch.markers))
    MarkerSemantics = tuple((MarkerCurve(Marker) for Marker in Sketch.markers))
    CurveRefIndices = {
        RefValue
        for Marker, Semantic in zip(Sketch.markers, MarkerSemantics, strict=True)
        for RefValue in MarkerCurveRef(Marker, Semantic)
    } | {
        RefValue
        for Marker in Sketch.markers
        for RefValue in MarkerObjectRef(Marker.data)
    }
    MarkerEntities: dict[int, str] = {}
    for MarkerIndex, (Marker, Semantic) in enumerate(
        zip(Sketch.markers, MarkerSemantics, strict=True)
    ):
        if Marker.offset in ProfileOffsets:
            EntityId = ProfileEntities.get(Marker.offset)
            if EntityId is not None:
                MarkerEntities[MarkerIndex] = EntityId
            continue
        if (
            MarkerIndex in CurveRefIndices
            and Marker.coordinates_mm is not None
            and (Marker.locus == "05000100")
        ):
            continue
        if (
            Marker.coordinates_mm is not None
            and Marker.object_index is None
            and (Marker.locus == "05000100")
        ):
            continue
        if Marker.endpoint_indices is None and b"sgSlot_c" in Marker.data:
            continue
        Entity = MarkerEntity(
            Sketch, Marker, CoordinatesByPrefix, CoordinatesByIndex, Semantic
        )
        Entities.append(Entity)
        MarkerEntities[MarkerIndex] = Entity.id
    return (Entities, MarkerEntities)


# this definition exists because dimension operands extend marker reference lookup
def MarkerRefsMut(
    Sketch: NativeSketch,
    MarkerEntities: Mapping[int, str],
    RefMapMut: dict[str, str],
) -> None:
    for Dimension in Sketch.dimensions:
        if Dimension.kind != "length":
            continue
        for Operand in Dimension.operands:
            EntityId = MarkerEntities.get(Operand.entity_index)
            if EntityId is not None:
                RefMapMut[f"native:{Operand.kind_code:04x}:{Operand.entity_index}"] = (
                    EntityId
                )


# this definition exists because profile loops need canonical closed entity groups
def ClosedSketch(Sketch: NativeSketch) -> tuple[tuple[str, ...], ...]:
    ClosedProfiles: list[tuple[str, ...]] = []
    for ProfileIndex, Profile in enumerate(Sketch.profiles):
        if Profile.kind == "rectangle":
            ClosedProfiles.append(
                tuple(
                    (
                        ProfileEdgeId(Sketch.object_id, ProfileIndex, EdgeIndex)
                        for EdgeIndex in range(4)
                    )
                )
            )
        elif Profile.kind == "circle":
            ClosedProfiles.append((ProfileId(Sketch.object_id, ProfileIndex),))
    return tuple(ClosedProfiles)


# this definition exists because focused behavior needs one stable owner
def SketchA(Sketch: NativeSketch, ParamIds: set[str]) -> SketchData:
    Entities, RefMap, ProfileEntities, ProfileOffsets = ProfileSketch(Sketch)
    MarkerValues, MarkerEntities = SketchMarkers(
        Sketch, ProfileOffsets, ProfileEntities
    )
    Entities.extend(MarkerValues)
    RefMap.update(
        {
            f"native-index:{Index}": EntityId
            for Index, EntityId in MarkerEntities.items()
        }
    )
    MarkerRefsMut(Sketch, MarkerEntities, RefMap)
    Constraints = SketchB(Sketch, RefMap, ParamIds)
    ClosedProfiles = ClosedSketch(Sketch)
    SketchParamIds = tuple(
        (
            ParamId
            for _, ParamId in ParamEntries(Sketch.object_id, Sketch.dimensions)
            if ParamId in ParamIds
        )
    )
    return SketchData(
        id=SketchId(Sketch.object_id),
        name=Sketch.name,
        support_plane_id=PlaneId(Sketch.support_plane_id),
        entities=tuple(Entities),
        constraints=Constraints,
        parameter_ids=SketchParamIds,
        closed_profile_entity_ids=ClosedProfiles,
        provenance=FeatureSpan(Sketch),
        attributes=FrozenMapping(
            {
                "native_object_id": Sketch.object_id,
                "native_marker_count": len(Sketch.markers),
                "native_profile_count": len(Sketch.profiles),
                "support_plane_native_id": Sketch.support_plane_id,
                "support_plane_source": Sketch.support_source,
                "unframed_support_plane_native_id": Sketch.unframed_support_plane_id,
            }
        ),
    )


# this definition exists because point and line markers share coordinate resolution
def MarkerLinear(
    Marker: NativeMarker,
    CoordinatesByPrefix: dict[str, tuple[tuple[float, float] | None, ...]],
    CoordinatesByIndex: tuple[tuple[float, float] | None, ...],
    ResolvedSemantic: str,
) -> tuple[GeomKind, KGeometryTypes] | None:
    if ResolvedSemantic == "point" and Marker.coordinates_mm is not None:
        return (GeomKind.POINT, PointGeom(VectorTwo(*Marker.coordinates_mm)))
    if ResolvedSemantic != "line" or Marker.endpoint_indices is None:
        return None
    Coordinates = (
        CoordinatesByIndex
        if ResolvedSemantic != Marker.semantic
        or (Marker.profile_role == 2 and Marker.native_kind == 2)
        else CoordinatesByPrefix[Marker.prefix]
    )
    Start = CoordinateRef(Coordinates, Marker.endpoint_indices[0])
    EndValue = CoordinateRef(Coordinates, Marker.endpoint_indices[1])
    if Start is not None and EndValue is not None and (Start != EndValue):
        return (GeomKind.LINE, LineGeom(VectorTwo(*Start), VectorTwo(*EndValue)))
    return (GeomKind.NATIVE, NativeMarkerA(Marker))


# this definition exists because curved markers share native fallback semantics
def MarkerCurved(
    Marker: NativeMarker,
    CoordinatesByIndex: tuple[tuple[float, float] | None, ...],
    ResolvedSemantic: str,
) -> tuple[GeomKind, KGeometryTypes]:
    KindValue = GeomKind.NATIVE
    GeomValue: KGeometryTypes | None = None
    if ResolvedSemantic in {"circle", "arc"}:
        Circular = MarkerCircular(Marker, CoordinatesByIndex, ResolvedSemantic)
        if Circular is not None:
            return Circular
    elif ResolvedSemantic == "ellipse":
        KindValue = GeomKind.ELLIPSE
        GeomValue = MarkerEllipse(Marker, CoordinatesByIndex)
    elif ResolvedSemantic == "arc_ellipse":
        KindValue = GeomKind.ARC_ELLIPSE
        GeomValue = MarkerArcGeom(Marker, CoordinatesByIndex)
    elif ResolvedSemantic == "parabola":
        KindValue = GeomKind.ARC_PARABOLA
        GeomValue = MarkerParabola(Marker, CoordinatesByIndex)
    elif ResolvedSemantic == "spline":
        KindValue = GeomKind.SPLINE
        GeomValue = MarkerSpline(Marker, CoordinatesByIndex)
    if GeomValue is None:
        return (GeomKind.NATIVE, NativeMarkerA(Marker, ResolvedSemantic))
    return (KindValue, GeomValue)


# this definition exists because marker geometry needs ordered semantic dispatch
def MarkerGeometry(
    Marker: NativeMarker,
    CoordinatesByPrefix: dict[str, tuple[tuple[float, float] | None, ...]],
    CoordinatesByIndex: tuple[tuple[float, float] | None, ...],
    ResolvedSemantic: str,
) -> tuple[GeomKind, KGeometryTypes]:
    Linear = MarkerLinear(
        Marker, CoordinatesByPrefix, CoordinatesByIndex, ResolvedSemantic
    )
    if Linear is not None:
        return Linear
    return MarkerCurved(Marker, CoordinatesByIndex, ResolvedSemantic)


# this definition exists because focused behavior needs one stable owner
def MarkerEntity(
    Sketch: NativeSketch,
    Marker: NativeMarker,
    CoordinatesByPrefix: dict[str, tuple[tuple[float, float] | None, ...]],
    CoordinatesByIndex: tuple[tuple[float, float] | None, ...],
    Semantic: str | None = None,
) -> SketchEntity:
    EntityId = MarkerId(Sketch.object_id, Marker.offset)
    ResolvedSemantic = Semantic or Marker.semantic
    KindValue, GeomValue = MarkerGeometry(
        Marker, CoordinatesByPrefix, CoordinatesByIndex, ResolvedSemantic
    )
    return SketchEntity(
        id=EntityId,
        kind=KindValue,
        geometry=GeomValue,
        construction=Marker.construction,
        provenance=ProvenanceA(
            f"{Sketch.object_id}:{Marker.offset}",
            Marker.offset,
            Marker.length,
            "sketch-native-marker",
            Stream=Sketch.native_stream,
        ),
        attributes=FrozenMapping(
            {
                "native_kind": Marker.native_kind,
                "native_locus": Marker.locus,
                "profile_role": Marker.profile_role,
                "state": Marker.state,
                "object_index": Marker.object_index,
                "local_id": Marker.local_id,
                "endpoint_indices": Marker.endpoint_indices,
                "semantic": ResolvedSemantic,
                "marker_prefix": Marker.prefix,
            }
        ),
    )


# this definition exists because focused behavior needs one stable owner
def MarkerCurve(Marker: NativeMarker) -> str:
    Endpoints = Marker.endpoint_indices
    if Endpoints is None:
        return Marker.semantic
    if Marker.semantic == "line" and b"cptsSplineList_c" not in Marker.data[:192]:
        return "line"
    if len(Marker.data) >= 102 and Marker.data[86:102] == b"\xfe\xff\xff\xff" * 4:
        return "circle" if Endpoints[0] == Endpoints[1] else "arc"
    if (
        Marker.length == 92 or (Marker.length == 104 and Endpoints[0] != Endpoints[1])
    ) and (Marker.locus == "05000100" or Marker.profile_role == 1):
        return "line"
    if Marker.length in {112, 116}:
        return "circle" if Endpoints[0] == Endpoints[1] else "arc"
    if Marker.length == 104:
        return "ellipse"
    if Marker.length == 108:
        return "arc_ellipse"
    if Marker.length == 124:
        return "parabola"
    if Marker.length == 128:
        return "conic"
    if Marker.length > 128:
        return "spline"
    return Marker.semantic


# this definition exists because focused behavior needs one stable owner
def MarkerCurveRef(Marker: NativeMarker, Semantic: str) -> tuple[int, ...]:
    Result = list(Marker.endpoint_indices or ())
    if Semantic in {"circle", "arc"} and len(Marker.data) >= 86:
        Result.append(Struct.unpack_from("<H", Marker.data, 84)[0])
    elif Semantic in {"ellipse", "arc_ellipse"} and len(Marker.data) >= 94:
        Result.extend(Struct.unpack_from("<5H", Marker.data, 84))
    elif Semantic == "parabola" and len(Marker.data) >= 88:
        Result.extend(Struct.unpack_from("<2I", Marker.data, 80))
    elif Semantic == "conic" and len(Marker.data) >= 96:
        Result.extend(Struct.unpack_from("<2I", Marker.data, 88))
    elif Semantic == "spline":
        Result.extend(MarkerSplineRef(Marker.data))
    return tuple(dict.fromkeys(Result))


# this definition exists because focused behavior needs one stable owner
def MarkerSplineRef(DataValue: bytes) -> tuple[int, ...]:
    Result: list[int] = []
    for Offset in range(max(0, len(DataValue) - 11)):
        if DataValue[Offset : Offset + 2] != b"\xa7\x80":
            continue
        if DataValue[Offset + 4 : Offset + 12] != b"\xff\xff\xff\xff\x00\x00\x00\x00":
            continue
        Result.append(Struct.unpack_from("<H", DataValue, Offset + 2)[0])
    return tuple(dict.fromkeys(Result))


# this definition exists because focused behavior needs one stable owner
def MarkerObjectRef(DataValue: bytes) -> tuple[int, ...]:
    Result: list[int] = []
    for Offset in range(max(0, len(DataValue) - 11)):
        if (
            DataValue[Offset] not in {167, 178, 183, 199}
            or DataValue[Offset + 1] != 128
        ):
            continue
        if DataValue[Offset + 4 : Offset + 12] != b"\xff\xff\xff\xff\x00\x00\x00\x00":
            continue
        Result.append(Struct.unpack_from("<H", DataValue, Offset + 2)[0])
    return tuple(dict.fromkeys(Result))


# this definition exists because focused behavior needs one stable owner
def MarkerCircular(
    Marker: NativeMarker,
    Coordinates: tuple[tuple[float, float] | None, ...],
    Semantic: str,
) -> tuple[GeomKind, CircleGeom | ArcGeom] | None:
    if Marker.endpoint_indices is None or len(Marker.data) < 86:
        return None
    Center = CoordinateRef(Coordinates, Struct.unpack_from("<H", Marker.data, 84)[0])
    Start = CoordinateRef(Coordinates, Marker.endpoint_indices[0])
    EndValue = CoordinateRef(Coordinates, Marker.endpoint_indices[1])
    if Center is None or Start is None:
        return None
    Radius = MathValue.dist(Center, Start)
    if not MathValue.isfinite(Radius) or Radius <= 1e-12:
        return None
    if Semantic == "circle":
        return (GeomKind.CIRCLE, CircleGeom(VectorTwo(*Center), Radius))
    if EndValue is None:
        return None
    StartAngle = MathValue.atan2(Start[1] - Center[1], Start[0] - Center[0])
    EndAngle = MathValue.atan2(EndValue[1] - Center[1], EndValue[0] - Center[0])
    if Struct.unpack_from("<I", Marker.data, 80)[0] == 4294967295:
        StartAngle, EndAngle = (EndAngle, StartAngle)
    return (GeomKind.ARC, ArcGeom(VectorTwo(*Center), Radius, StartAngle, EndAngle))


# this definition exists because focused behavior needs one stable owner
def MarkerEllipse(
    Marker: NativeMarker, Coordinates: tuple[tuple[float, float] | None, ...]
) -> EllipseGeom | None:
    if len(Marker.data) < 90:
        return None
    CenterIndex, MajorIndex, MinorIndex = Struct.unpack_from("<3H", Marker.data, 84)
    Center = CoordinateRef(Coordinates, CenterIndex)
    Major = CoordinateRef(Coordinates, MajorIndex)
    Minor = CoordinateRef(Coordinates, MinorIndex)
    if Center is None or Major is None or Minor is None:
        return None
    MajorRadius = MathValue.dist(Center, Major)
    MinorRadius = MathValue.dist(Center, Minor)
    if MajorRadius <= 1e-12 or MinorRadius <= 1e-12:
        return None
    return EllipseGeom(
        VectorTwo(*Center),
        VectorTwo(
            (Major[0] - Center[0]) / MajorRadius, (Major[1] - Center[1]) / MajorRadius
        ),
        MajorRadius,
        MinorRadius,
    )


# this definition exists because focused behavior needs one stable owner
def MarkerArcGeom(
    Marker: NativeMarker, Coordinates: tuple[tuple[float, float] | None, ...]
) -> ArcEllipseGeom | None:
    Ellipse = MarkerEllipse(Marker, Coordinates)
    if Ellipse is None or Marker.endpoint_indices is None:
        return None
    Start = CoordinateRef(Coordinates, Marker.endpoint_indices[0])
    EndValue = CoordinateRef(Coordinates, Marker.endpoint_indices[1])
    if Start is None or EndValue is None:
        return None
    FirstParam = Ellipse.major_axis
    SecondParam = VectorTwo(-FirstParam.y, FirstParam.x)

    # this definition exists because focused behavior needs one stable owner
    def Param(Point: tuple[float, float]) -> float:
        Delta = VectorTwo(Point[0] - Ellipse.center.x, Point[1] - Ellipse.center.y)
        return MathValue.atan2(
            (Delta.x * SecondParam.x + Delta.y * SecondParam.y) / Ellipse.minor_radius,
            (Delta.x * FirstParam.x + Delta.y * FirstParam.y) / Ellipse.major_radius,
        )

    return ArcEllipseGeom(
        Ellipse.center,
        Ellipse.major_axis,
        Ellipse.major_radius,
        Ellipse.minor_radius,
        Param(Start),
        Param(EndValue),
    )


# this definition exists because focused behavior needs one stable owner
def MarkerSpline(
    Marker: NativeMarker, Coordinates: tuple[tuple[float, float] | None, ...]
) -> SplineGeom | None:
    References = MarkerSplineRef(Marker.data)
    Points = tuple(
        (
            Point
            for Index in References
            if (Point := CoordinateRef(Coordinates, Index)) is not None
        )
    )
    if len(Points) < 2:
        return None
    Degree = min(3, len(Points) - 1)
    return SplineGeom(tuple((VectorTwo(*Point) for Point in Points)), Degree)


# this definition exists because focused behavior needs one stable owner
def MarkerParabola(
    Marker: NativeMarker, Coordinates: tuple[tuple[float, float] | None, ...]
) -> ArcParabolaGeom | None:
    if Marker.endpoint_indices is None or len(Marker.data) < 88:
        return None
    FocusIndex, ApexIndex = Struct.unpack_from("<2I", Marker.data, 80)
    Focus = CoordinateRef(Coordinates, FocusIndex)
    ApexValue = CoordinateRef(Coordinates, ApexIndex)
    Start = CoordinateRef(Coordinates, Marker.endpoint_indices[0])
    EndValue = CoordinateRef(Coordinates, Marker.endpoint_indices[1])
    if Focus is None or ApexValue is None or Start is None or (EndValue is None):
        return None
    FocalLength = MathValue.dist(Focus, ApexValue)
    if not MathValue.isfinite(FocalLength) or FocalLength <= 1e-12:
        return None
    AxisValue = VectorTwo(
        (Focus[0] - ApexValue[0]) / FocalLength, (Focus[1] - ApexValue[1]) / FocalLength
    )
    Perpendicular = VectorTwo(-AxisValue.y, AxisValue.x)

    # this definition exists because focused behavior needs one stable owner
    def Param(Point: tuple[float, float]) -> float:
        Delta = VectorTwo(Point[0] - ApexValue[0], Point[1] - ApexValue[1])
        return (Delta.x * Perpendicular.x + Delta.y * Perpendicular.y) / (
            2.0 * FocalLength
        )

    Limits = sorted((Param(Start), Param(EndValue)))
    return ArcParabolaGeom(
        VectorTwo(*ApexValue), AxisValue, FocalLength, Limits[0], Limits[1]
    )


# this definition exists because focused behavior needs one stable owner
def CoordinateRef(
    Coordinates: tuple[tuple[float, float] | None, ...], Index: int
) -> tuple[float, float] | None:
    return Coordinates[Index] if 0 <= Index < len(Coordinates) else None


# this definition exists because focused behavior needs one stable owner
def NativeMarkerA(Marker: NativeMarker, EntityType: str | None = None) -> NativeGeom:
    return NativeGeom(
        format_id=KFormatId,
        entity_type=EntityType or Marker.semantic,
        data=FrozenMapping(
            {
                "native_kind": Marker.native_kind,
                "locus": Marker.locus,
                "coordinates_mm": Marker.coordinates_mm,
                "endpoint_indices": Marker.endpoint_indices,
                "record_data": Marker.data,
            }
        ),
    )


# this state exists because sketch rule resolution shares occurrence counters
@DataClass(slots=True)
class RuleContext:
    Candidates: Mapping[float, list[tuple[str, str]]]
    DimensionsByName: Mapping[str, list[NativeDimension]]
    ParamIdsByName: Mapping[str, list[str]]
    DimensionUsage: Defaultdict[float, int]
    ParamUsage: Defaultdict[str, int]
    RuleIdUsage: Defaultdict[str, int]
    ParamIds: set[str]


# this definition exists because rule resolution needs indexed dimensions and profiles
def RuleContextA(Sketch: NativeSketch, ParamIds: set[str]) -> RuleContext:
    Candidates: Defaultdict[float, list[tuple[str, str]]] = Defaultdict(list)
    for ProfileIndex, Profile in enumerate(Sketch.profiles):
        if Profile.kind != "rectangle":
            continue
        Width = round(Profile.coordinates[2] - Profile.coordinates[0], 9)
        Height = round(Profile.coordinates[3] - Profile.coordinates[1], 9)
        Candidates[Width].append(
            (ProfileEdgeId(Sketch.object_id, ProfileIndex, 0), "distance_x")
        )
        Candidates[Height].append(
            (ProfileEdgeId(Sketch.object_id, ProfileIndex, 1), "distance_y")
        )
    DimensionsByName: Defaultdict[str, list[NativeDimension]] = Defaultdict(list)
    ParamIdsByName: Defaultdict[str, list[str]] = Defaultdict(list)
    for Dimension, ParamId in ParamEntries(Sketch.object_id, Sketch.dimensions):
        DimensionsByName[Dimension.name].append(Dimension)
        ParamIdsByName[Dimension.name].append(ParamId)
    return RuleContext(
        Candidates,
        DimensionsByName,
        ParamIdsByName,
        Defaultdict(int),
        Defaultdict(int),
        Defaultdict(int),
        ParamIds,
    )


# this definition exists because each native rule needs deterministic occurrence binding
def RulePartsMut(
    RuleValue: NativeRule, RefMap: Mapping[str, str], ContextMut: RuleContext
) -> tuple[
    list[RuleRef],
    str,
    str,
    int,
    NativeDimension | None,
    str | None,
    str,
]:
    ResolvedRefs = [RefMap.get(RefValue) for RefValue in RuleValue.references]
    References = (
        [RuleRef(Resolved) for Resolved in ResolvedRefs if Resolved is not None]
        if ResolvedRefs and all(ResolvedRefs)
        else []
    )
    KindValue = RuleValue.kind
    NativeName = (
        RuleValue.parameter.rsplit(":", 1)[-1]
        if RuleValue.parameter is not None
        else ""
    )
    ItemValue = ContextMut.ParamUsage[NativeName] if NativeName else 0
    Dimensions = ContextMut.DimensionsByName.get(NativeName, [])
    Dimension = Dimensions[min(ItemValue, len(Dimensions) - 1)] if Dimensions else None
    if not References and RuleValue.parameter is not None and Dimension is not None:
        KeyValue = round(Dimension.value_mm, 9)
        Available = ContextMut.Candidates.get(KeyValue, [])
        if Available:
            Index = ContextMut.DimensionUsage[KeyValue] % len(Available)
            EntityId, KindValue = Available[Index]
            ContextMut.DimensionUsage[KeyValue] += 1
            References = [RuleRef(EntityId)]
    ParamId = None
    if RuleValue.parameter is not None:
        AvailableIds = ContextMut.ParamIdsByName.get(NativeName, [])
        if AvailableIds:
            Choice = AvailableIds[min(ItemValue, len(AvailableIds) - 1)]
            ParamId = Choice if Choice in ContextMut.ParamIds else None
        ContextMut.ParamUsage[NativeName] += 1
    ContextMut.RuleIdUsage[RuleValue.id] += 1
    RuleId = f"sldprt:constraint:{RuleValue.id}"
    if ContextMut.RuleIdUsage[RuleValue.id] > 1:
        RuleId += f":{ContextMut.RuleIdUsage[RuleValue.id]}"
    return (References, KindValue, NativeName, ItemValue, Dimension, ParamId, RuleId)


# this definition exists because resolved rule parts need one neutral constructor
def BuildSketchRule(
    Sketch: NativeSketch,
    RuleValue: NativeRule,
    RefMap: Mapping[str, str],
    ContextMut: RuleContext,
) -> SketchRule:
    References, KindValue, NativeName, ItemValue, Dimension, ParamId, RuleId = (
        RulePartsMut(RuleValue, RefMap, ContextMut)
    )
    return SketchRule(
        id=RuleId,
        kind=KindValue,
        references=tuple(References),
        parameter_id=ParamId,
        driving=Dimension.native_role != "display" if Dimension else True,
        provenance=(
            ProvenanceA(
                RuleValue.id,
                RuleValue.native_offset,
                8,
                "sketch-constraint",
                Stream=Sketch.native_stream,
            )
            if RuleValue.native_offset is not None
            else None
        ),
        attributes=FrozenMapping(
            {
                "native_code": RuleValue.native_code,
                "native_references": RuleValue.references,
                "native_value": RuleValue.value,
                "parameter_occurrence": ItemValue + 1 if NativeName else None,
            }
        ),
    )


# this definition exists because rectangle closure needs inferred coincidence rules
def ProfileRules(Sketch: NativeSketch) -> tuple[SketchRule, ...]:
    Result: list[SketchRule] = []
    for ProfileIndex, Profile in enumerate(Sketch.profiles):
        if Profile.kind != "rectangle":
            continue
        for EdgeIndex in range(4):
            Current = ProfileEdgeId(Sketch.object_id, ProfileIndex, EdgeIndex)
            Following = ProfileEdgeId(
                Sketch.object_id, ProfileIndex, (EdgeIndex + 1) % 4
            )
            Result.append(
                SketchRule(
                    id=f"sldprt:constraint:{Sketch.object_id}:profile:{ProfileIndex}:coincident:{EdgeIndex}",
                    kind="coincident",
                    references=(RuleRef(Current, "end"), RuleRef(Following, "start")),
                    attributes=FrozenMapping({"inferred": True}),
                )
            )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def SketchB(
    Sketch: NativeSketch, RefMap: dict[str, str], ParamIds: set[str]
) -> tuple[SketchRule, ...]:
    ContextMut = RuleContextA(Sketch, ParamIds)
    ExplicitRules = tuple(
        (
            BuildSketchRule(Sketch, RuleValue, RefMap, ContextMut)
            for RuleValue in Sketch.constraints
        )
    )
    return (*ExplicitRules, *ProfileRules(Sketch))


# this definition exists because focused behavior needs one stable owner
def Selections(Model: NativeModel) -> tuple[Selection, ...]:
    Result: list[Selection] = []
    for Operation in Model.operations:
        if not Operation.selection_offsets:
            continue
        for Producer, LocalId, Offsets in OperationA(Operation):
            SelectionId = OperationId(Operation, Producer, LocalId)
            KindValue = Operation.selection_kind
            Result.append(
                Selection(
                    id=SelectionId,
                    name=f"{Operation.name} {KindValue} {LocalId}",
                    path=(
                        SelectionPathElem(
                            entity_kind="feature",
                            entity_id=FeatureId(Producer),
                            subelement=f"{KindValue}:{LocalId}",
                        ),
                    ),
                    query=FrozenMapping(
                        {
                            "native_producer_id": Producer,
                            "native_local_id": LocalId,
                            "native_identity": "7dc39425ad49b2547dc39425ad49b254",
                            "topology_role": (
                                "extrusion_terminal_profile_boundary"
                                if Operation.kind == "fillet"
                                else f"native_{KindValue}"
                            ),
                        }
                    ),
                    provenance=Provenance(
                        adapter=KFormatId,
                        native_id=f"{Operation.object_id}:{KindValue}:{LocalId}",
                        spans=tuple(
                            (
                                ProvenanceSpan(
                                    Operation.native_stream,
                                    Offset,
                                    38,
                                    f"{KindValue}-selection",
                                )
                                for Offset in Offsets
                            )
                        ),
                    ),
                )
            )
    return (*Result, *DirectionAxis(Model))


# this definition exists because focused behavior needs one stable owner
def DirectionAxis(Model: NativeModel) -> tuple[Selection, ...]:
    SketchById = {Sketch.object_id: Sketch for Sketch in Model.sketches}
    Result: list[Selection] = []
    for Operation in Model.operations:
        AxisId = AxisSketchId(
            Operation.profile_id, Operation.axis_source_kind, Operation.axis_source_id
        )
        if AxisId is None:
            continue
        Sketch = SketchById.get(AxisId)
        SubElem = OperationAxisSubElem(Operation, Sketch)
        if Sketch is None or SubElem is None:
            continue
        Result.append(
            Selection(
                id=f"sldprt:selection:{Operation.object_id}:axis:{Sketch.object_id}:{SubElem}",
                name=f"{Operation.name} direction {SubElem}",
                path=(
                    SelectionPathElem(
                        entity_kind="native", entity_id=Sketch.name, subelement=SubElem
                    ),
                ),
                query=FrozenMapping(
                    {
                        "native_owner_id": Operation.object_id,
                        "native_target_id": Sketch.object_id,
                        "topology_role": DirectionAxisRole,
                    }
                ),
                provenance=Provenance(
                    adapter=KFormatId,
                    native_id=f"{Operation.object_id}:axis:{SubElem}",
                    spans=(
                        ProvenanceSpan(
                            Operation.native_stream,
                            Operation.native_offset,
                            Operation.native_end - Operation.native_offset,
                            "direction-axis",
                        ),
                    ),
                ),
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def OperationA(
    Operation: NativeOperation,
) -> tuple[tuple[int, int, tuple[int, ...]], ...]:
    References = Operation.selection_references
    if not References:
        Producer = Operation.dependencies[-1] if Operation.dependencies else 0
        References = tuple(
            ((Producer, LocalId) for LocalId in Operation.selected_local_ids)
        )
    Aligned = len(Operation.selection_offsets) == len(References)
    return tuple(
        (
            (
                Producer,
                LocalId,
                (
                    (Operation.selection_offsets[Index],)
                    if Aligned
                    else Operation.selection_offsets
                ),
            )
            for Index, (Producer, LocalId) in enumerate(References)
        )
    )


# this definition exists because focused behavior needs one stable owner
def OperationId(Operation: NativeOperation, Producer: int, LocalId: int) -> str:
    Duplicate = (
        sum((RefLocal == LocalId for _, RefLocal in Operation.selection_references)) > 1
    )
    return SelectionId(
        Operation.object_id,
        LocalId,
        Operation.selection_kind,
        Producer if Duplicate else None,
    )


# this definition exists because focused behavior needs one stable owner
def TimelineInputs(
    Feature: NativeFeature,
    Operation: NativeOperation | None,
    Sketch: NativeSketch | None,
    PlaneById: Mapping[int, NativePlane],
    PrincipalIds: set[int],
    PreviousValue: int | None,
) -> list[int]:
    if Operation is not None:
        return list(Operation.dependencies)
    if Sketch is not None:
        return [Sketch.support_plane_id]
    if Feature.object_id not in PlaneById:
        return []
    RefIds = list(PlaneById[Feature.object_id].reference_ids)
    if (
        not RefIds
        and Feature.object_id not in PrincipalIds
        and PreviousValue is not None
    ):
        RefIds.append(PreviousValue)
    return RefIds


# this definition exists because operation kinds need neutral boolean semantics
def TimelineOp(
    Operation: NativeOperation | None, SelectionIds: set[str]
) -> tuple[BoolOperation | str | None, tuple[str, ...]]:
    if Operation is None:
        return (None, ())
    KindMap: dict[str, BoolOperation | None] = {
        "join": BoolOperation.JOIN,
        "cut": BoolOperation.CUT,
        "revolve_join": BoolOperation.JOIN,
        "revolve_cut": BoolOperation.CUT,
        "hole": BoolOperation.CUT,
        "combine_join": BoolOperation.JOIN,
        "surface": BoolOperation.CREATE,
        "fillet": None,
        "chamfer": None,
        "shell": None,
        "dome": None,
        "scale": None,
        "move_body": None,
    }
    OperationValue = KindMap.get(Operation.kind, Operation.kind)
    Selected = tuple(
        (
            SelectionId
            for Producer, LocalId, _ in OperationA(Operation)
            for SelectionId in (OperationId(Operation, Producer, LocalId),)
            if SelectionId in SelectionIds
        )
    )
    return (OperationValue, Selected)


# this definition exists because focused behavior needs one stable owner
def Timeline(
    Model: NativeModel, Selections: tuple[Selection, ...]
) -> tuple[FeatureStep, ...]:
    OperationById = {Operation.object_id: Operation for Operation in Model.operations}
    SketchById = {Sketch.object_id: Sketch for Sketch in Model.sketches}
    PlaneById = {Plane.object_id: Plane for Plane in Model.planes}
    FeatureIds = {Feature.object_id for Feature in Model.features}
    OrderById = {
        Feature.object_id: Order for Order, Feature in enumerate(Model.features)
    }
    SelectionIds = {Selection.id for Selection in Selections}
    PrincipalPlaneIds = {Plane.object_id for Plane in Model.planes if Plane.principal}
    PreviousOperation: int | None = None
    Result: list[FeatureStep] = []
    for Order, Feature in enumerate(Model.features):
        Operation = OperationById.get(Feature.object_id)
        Sketch = SketchById.get(Feature.object_id)
        Inputs = TimelineInputs(
            Feature, Operation, Sketch, PlaneById, PrincipalPlaneIds, PreviousOperation
        )
        Dependencies = tuple(
            (
                FeatureId(NativeId)
                for NativeId in dict.fromkeys(Inputs)
                if NativeId in FeatureIds and OrderById[NativeId] < Order
            )
        )
        ParamIds = tuple(
            (
                ParamId
                for _, ParamId in ParamEntries(Feature.object_id, Feature.dimensions)
            )
        )
        Attributes: dict[str, object] = {
            "native_object_id": Feature.object_id,
            "native_type": Feature.kind,
            "xml_tag": Feature.xml_tag,
            "native_properties": Feature.properties,
        }
        OperationValue, Selected = TimelineOp(Operation, SelectionIds)
        if Operation is not None:
            Attributes.update(OperationAttrs(Operation))
            if Operation.kind != "surface":
                PreviousOperation = Operation.object_id
        Result.append(
            FeatureStep(
                id=FeatureId(Feature.object_id),
                name=Feature.name,
                kind=FeatureKindA(Feature),
                order=Order,
                input_feature_ids=Dependencies,
                sketch_id=(
                    SketchId(Operation.profile_id)
                    if Operation is not None and Operation.profile_id in SketchById
                    else SketchId(Feature.object_id) if Sketch is not None else None
                ),
                parameter_ids=ParamIds,
                operation=OperationValue,
                definition=BuildFeature(Feature, Operation, SketchById, PlaneById),
                selection_ids=Selected,
                provenance=FeatureA(Feature),
                attributes=FrozenMapping(Attributes),
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def SolidBody(Features: tuple[NativeFeature, ...]) -> NativeFeature | None:
    return next(
        (
            Feature
            for Feature in Features
            if Feature.kind.casefold().strip() in SolidBodyFeatureTypes
        ),
        None,
    )


# this definition exists because focused behavior needs one stable owner
def FinalBodyId(
    Timeline: tuple[FeatureStep, ...], OperationFeatureIds: frozenset[str]
) -> str:
    Choice = next(
        (
            Feature
            for Feature in reversed(Timeline)
            if Feature.id in OperationFeatureIds
            or (
                isinstance(Feature.kind, FeatureKind)
                and Feature.kind != FeatureKind.REFERENCE
                and (Feature.kind != FeatureKind.SURFACE)
                and (Feature.kind != FeatureKind.NATIVE)
            )
        ),
        None,
    )
    if Choice is not None:
        return Choice.id
    return Timeline[-1].id if Timeline else ""


# this definition exists because focused behavior needs one stable owner
def OperationAttrs(Operation: NativeOperation) -> dict[str, object]:
    Result: dict[str, object] = {
        "profile_native_id": Operation.profile_id,
        "native_dependencies": Operation.dependencies,
        "family_code": Operation.family_code,
        "operation_code": Operation.operation_code,
        "schema_code": Operation.schema_code,
        "direction_code": Operation.direction_code,
        "termination_code": Operation.termination_code,
        "native_selection_offsets": Operation.selection_offsets,
        "selected_local_ids": Operation.selected_local_ids,
        "native_selection_references": Operation.selection_references,
        "selection_kind": Operation.selection_kind,
        "mode": Operation.mode,
    }
    if Operation.length_mm is not None:
        Result.update(
            {
                "length_mm": Operation.length_mm,
                "direction_multiplier": (
                    -1 if Operation.kind in {"cut", "revolve_cut", "hole"} else 1
                ),
                "end_condition": (
                    "blind"
                    if Operation.termination_code == 0
                    else f"native:{Operation.termination_code}"
                ),
            }
        )
    if Operation.radius_mm is not None:
        Result["radius_mm"] = Operation.radius_mm
    if Operation.angle_degrees is not None:
        Result["angle_degrees"] = Operation.angle_degrees
    if Operation.diameter_mm is not None:
        Result["diameter_mm"] = Operation.diameter_mm
    if Operation.second_length_mm is not None:
        Result["second_length_mm"] = Operation.second_length_mm
    if Operation.axis_marker_offset is not None:
        Result["axis_marker_offset"] = Operation.axis_marker_offset
    if Operation.axis_source_kind is not None:
        Result["axis_source_kind"] = Operation.axis_source_kind
    if Operation.axis_source_id is not None:
        Result["axis_source_id"] = Operation.axis_source_id
    if Operation.axis_source_offset is not None:
        Result["axis_source_offset"] = Operation.axis_source_offset
    if Operation.end_spec_offset is not None:
        Result["end_spec_offset"] = Operation.end_spec_offset
    if Operation.translation_mm is not None:
        Result["translation_mm"] = Operation.translation_mm
    if Operation.scale_factors is not None:
        Result["scale_factors"] = Operation.scale_factors
    return Result


# this definition exists because unknown features need lossless native metadata
def NativeFallback(
    Feature: NativeFeature, Operation: NativeOperation | None
) -> NativeFeatureDefinition:
    return NativeFeatureDefinition(
        format_id=KFormatId,
        type_id=Feature.kind or Feature.xml_tag,
        object_data=FrozenMapping(
            {
                "native_object_id": Feature.object_id,
                "native_class": Feature.class_name,
                "native_stream": Feature.native_stream,
                "xml_tag": Feature.xml_tag,
                "properties": Feature.properties,
                "dimensions": tuple(
                    (
                        {
                            "name": Dimension.name,
                            "value_mm": Dimension.value_mm,
                            "kind": Dimension.kind,
                            "source_text": Dimension.source_text,
                            "native_value": Dimension.native_value,
                            "native_offset": Dimension.native_offset,
                            "native_role": Dimension.native_role,
                            "operands": tuple(
                                (
                                    {
                                        "offset": Operand.offset,
                                        "kind_code": Operand.kind_code,
                                        "entity_index": Operand.entity_index,
                                    }
                                    for Operand in Dimension.operands
                                )
                            ),
                        }
                        for Dimension in Feature.dimensions
                    )
                ),
                "record_data": Feature.data,
                "operation": (
                    OperationAttrs(Operation) if Operation is not None else None
                ),
            }
        ),
    )


# this definition exists because focused behavior needs one stable owner
def BuildExtrude(Operation: NativeOperation | None) -> ExtrusionFeature | None:
    if (
        Operation is None
        or Operation.kind not in {"join", "cut", "surface"}
        or Operation.length_mm is None
    ):
        return None
    return ExtrusionFeature(
        length=ParamValue(Operation.length_mm, ValueKind.LENGTH, "mm"),
        end_condition=(
            ExtrusionEndCondition.BLIND
            if Operation.termination_code == 0
            else f"native:{Operation.termination_code}"
        ),
        reversed=Operation.kind == "cut",
        second_length=(
            ParamValue(Operation.second_length_mm, ValueKind.LENGTH, "mm")
            if Operation.second_length_mm is not None
            else None
        ),
    )


# this definition exists because detail operations share dimensional construction
def BuildDetail(
    Operation: NativeOperation | None,
) -> HoleFeature | FilletFeature | ChamferFeature | ShellFeature | None:
    if Operation is None:
        return None
    if (
        Operation.kind == "hole"
        and Operation.diameter_mm is not None
        and Operation.length_mm is not None
    ):
        return HoleFeature(
            diameter=ParamValue(Operation.diameter_mm, ValueKind.LENGTH, "mm"),
            depth=ParamValue(Operation.length_mm, ValueKind.LENGTH, "mm"),
        )
    if Operation.kind == "fillet" and Operation.radius_mm is not None:
        return FilletFeature(
            radius=ParamValue(Operation.radius_mm, ValueKind.LENGTH, "mm")
        )
    if (
        Operation.kind == "chamfer"
        and Operation.length_mm is not None
        and Operation.mode == "equal_distance"
    ):
        return ChamferFeature(
            distance=ParamValue(Operation.length_mm, ValueKind.LENGTH, "mm")
        )
    if Operation.kind == "shell" and Operation.length_mm is not None:
        return ShellFeature(
            thickness=ParamValue(Operation.length_mm, ValueKind.LENGTH, "mm")
        )
    return None


# this definition exists because focused behavior needs one stable owner
def BuildFeature(
    Feature: NativeFeature,
    Operation: NativeOperation | None,
    Sketches: Mapping[int, NativeSketch],
    Planes: Mapping[int, NativePlane],
) -> (
    ExtrusionFeature
    | FilletFeature
    | RevolutionFeature
    | HoleFeature
    | ChamferFeature
    | ShellFeature
    | RefPlaneFeature
    | DomeFeature
    | MoveBodyFeature
    | CombineFeature
    | ScaleFeature
    | NativeFeatureDefinition
):
    Extrusion = BuildExtrude(Operation)
    if Extrusion is not None:
        return Extrusion
    Revolution = BuildRevolve(Operation, Sketches)
    if Revolution is not None:
        return Revolution
    DetailValue = BuildDetail(Operation)
    if DetailValue is not None:
        return DetailValue
    if (
        Operation is not None
        and Operation.kind == "dome"
        and (Operation.length_mm is not None)
    ):
        return DomeFeature(
            height=ParamValue(Operation.length_mm, ValueKind.LENGTH, "mm")
        )
    if Operation is not None and Operation.kind == "move_body":
        Translation = Operation.translation_mm
        if Translation is not None:
            return MoveBodyFeature(translation=VectorThree(*Translation))
    if Operation is not None and Operation.kind == "combine_join":
        return CombineFeature(BoolOperation.JOIN)
    if Operation is not None and Operation.kind == "scale":
        Factors = Operation.scale_factors
        if Factors is not None:
            return ScaleFeature(VectorThree(*Factors))
    Plane = Planes.get(Feature.object_id)
    RefIds = Plane.reference_ids if Plane is not None else ()
    Offset = OperationValue(Feature.dimensions, "offset")
    if Plane is not None and len(RefIds) == 1 and (Offset is not None):
        return RefPlaneFeature(
            support_plane_id=PlaneId(Feature.object_id),
            reference_plane_id=PlaneId(RefIds[0]),
            offset=ParamValue(Offset, ValueKind.LENGTH, "mm"),
        )
    return NativeFallback(Feature, Operation)


# this definition exists because focused behavior needs one stable owner
def OperationValue(
    Dimensions: tuple[NativeDimension, ...], KindValue: str
) -> float | None:
    return next(
        (Dimension.value_mm for Dimension in Dimensions if Dimension.kind == KindValue),
        None,
    )


# this definition exists because focused behavior needs one stable owner
def FeatureKindA(Feature: NativeFeature | XmlFeature) -> FeatureKind:
    if getattr(Feature, "class_name", "") in {"moSketchHole", "moHoleWzd_c"}:
        return FeatureKind.HOLE
    return KFeatureKindByNative.get(Feature.kind.casefold().strip(), FeatureKind.NATIVE)


# this definition exists because focused behavior needs one stable owner
def BrepPayloads(
    Archive: SldprtArchive, Options: ReadOptions
) -> tuple[tuple[BrepPayload, ...], tuple[DiagValue, ...]]:
    if not Options.include_brep:
        return ((), ())
    Payloads: list[BrepPayload] = []
    Diagnostics: list[DiagValue] = []
    for Record in Archive.records:
        if not ContainsParasolidPayload(Record.data):
            continue
        try:
            Decoded = DecodePartitionStream(Record.data, Record.name)
        except SldprtFormatError as ErrorInfo:
            if Options.strict:
                raise
            Diagnostics.append(
                DiagValue(
                    code="sldprt.parasolid_decode_failed",
                    message=str(ErrorInfo),
                    severity=Severity.WARNING,
                    attributes=FrozenMapping({"stream": Record.name}),
                )
            )
            continue
        for Native in Decoded:
            Payloads.append(BrepPayloadA(len(Payloads), Native))
    if not Payloads and Options.strict:
        raise SldprtFormatError("SLDPRT contains no readable Parasolid payload")
    return (tuple(Payloads), tuple(Diagnostics))


# this definition exists because focused behavior needs one stable owner
def BrepPayloadA(Index: int, Native: ParasolidPayload) -> BrepPayload:
    return BrepPayload(
        id=f"sldprt:brep:{Index}",
        format_id="parasolid",
        kind=Native.kind,
        schema=Native.schema,
        sha256=Native.sha256,
        data=Native.data,
        source_stream=Native.stream,
        provenance=Provenance(
            adapter=KFormatId,
            native_id=f"{Native.stream}:{Native.wrapper_offset}",
            spans=(
                ProvenanceSpan(
                    Native.stream,
                    Native.wrapper_offset,
                    Native.stored_size,
                    "parasolid-wrapper",
                ),
            ),
        ),
        attributes=FrozenMapping(
            {
                "description": Native.description,
                "wrapper_offset": Native.wrapper_offset,
                "magic_offset": Native.magic_offset,
                "compressed_offset": Native.compressed_offset,
                "compressed_size": Native.compressed_size,
                "uncompressed_size": Native.uncompressed_size,
                "stored_size": Native.stored_size,
            }
        ),
        role=PayloadRole.BREP,
        file_extension=".x_b",
    )


# this definition exists because focused behavior needs one stable owner
def TypedBrep(Payloads: Sequence[BrepPayload]) -> BrepModel | None:
    Groups: dict[str, list[BrepPayload]] = {}
    for Index, Payload in enumerate(Payloads):
        Groups.setdefault(Payload.source_stream or f"payload:{Index}", []).append(
            Payload
        )
    Models: list[BrepModel] = []
    for Group in Groups.values():
        Decoded = tuple(
            (
                Model
                for Payload in Group
                if Payload.data is not None
                and (Model := DecodeBrepModel(Payload.data)) is not None
            )
        )
        if len(Decoded) == 1:
            Models.append(Decoded[0])
    return Models[0] if len(Models) == 1 else None


# this definition exists because focused behavior needs one stable owner
def BoundingBoxA(Model: NativeModel) -> BoundingBox | None:
    SketchById = {Sketch.object_id: Sketch for Sketch in Model.sketches}
    PlaneById = {Plane.object_id: Plane for Plane in Model.planes}
    Points: list[tuple[float, float, float]] = []
    for Operation in Model.operations:
        if Operation.kind != "join" or Operation.profile_id is None:
            continue
        Sketch = SketchById.get(Operation.profile_id)
        if Sketch is None:
            continue
        Plane = PlaneById.get(Sketch.support_plane_id)
        if Plane is None or Operation.length_mm is None:
            continue
        Direction = (
            Plane.normal[0] * Operation.length_mm,
            Plane.normal[1] * Operation.length_mm,
            Plane.normal[2] * Operation.length_mm,
        )
        for Profile in Sketch.profiles:
            for Local in ProfileExtrema(Profile):
                BaseValue = (
                    Plane.origin_mm[0]
                    + Plane.u_axis[0] * Local[0]
                    + Plane.v_axis[0] * Local[1],
                    Plane.origin_mm[1]
                    + Plane.u_axis[1] * Local[0]
                    + Plane.v_axis[1] * Local[1],
                    Plane.origin_mm[2]
                    + Plane.u_axis[2] * Local[0]
                    + Plane.v_axis[2] * Local[1],
                )
                Points.append(BaseValue)
                Points.append(
                    (
                        BaseValue[0] + Direction[0],
                        BaseValue[1] + Direction[1],
                        BaseValue[2] + Direction[2],
                    )
                )
    if not Points:
        return None
    return BoundingBox(
        minimum=VectorThree(
            *(min((Point[Index] for Point in Points)) for Index in range(3))
        ),
        maximum=VectorThree(
            *(max((Point[Index] for Point in Points)) for Index in range(3))
        ),
    )


# this definition exists because focused behavior needs one stable owner
def ProfileExtrema(Profile: NativeProfile) -> tuple[tuple[float, float], ...]:
    if Profile.kind == "rectangle":
        XZero, YZero, XOneValue, YOneValue = Profile.coordinates
        return (
            (XZero, YZero),
            (XZero, YOneValue),
            (XOneValue, YZero),
            (XOneValue, YOneValue),
        )
    if Profile.kind == "circle":
        FirstCoord, SecondCoord, Radius = Profile.coordinates
        return (
            (FirstCoord - Radius, SecondCoord),
            (FirstCoord + Radius, SecondCoord),
            (FirstCoord, SecondCoord - Radius),
            (FirstCoord, SecondCoord + Radius),
        )
    return ()


# this definition exists because focused behavior needs one stable owner
def FeatureA(Feature: NativeFeature) -> Provenance:
    return ProvenanceA(
        str(Feature.object_id),
        Feature.native_offset,
        (
            Feature.native_end - Feature.native_offset
            if Feature.native_offset is not None and Feature.native_end is not None
            else None
        ),
        "feature-record",
        Confidence=1.0 if Feature.native_offset is not None else 0.6,
        Stream=Feature.native_stream,
    )


# this definition exists because focused behavior needs one stable owner
def FeatureSpan(Sketch: NativeSketch) -> Provenance:
    return ProvenanceA(
        str(Sketch.object_id),
        Sketch.native_offset,
        Sketch.native_end - Sketch.native_offset,
        "sketch-record",
        Stream=Sketch.native_stream,
    )


# this definition exists because focused behavior needs one stable owner
def ProvenanceA(
    NativeId: str,
    Offset: int | None,
    Length: int | None,
    KindValue: str,
    *,
    Confidence: float = 1.0,
    Stream: str = ResolvedFeaturesStream,
) -> Provenance:
    Spans = (
        (ProvenanceSpan(Stream, Offset, Length or 0, KindValue),)
        if Offset is not None
        else ()
    )
    return Provenance(
        adapter=KFormatId, native_id=NativeId, confidence=Confidence, spans=Spans
    )


# this definition exists because focused behavior needs one stable owner
def ConfigId(NativeId: int) -> str:
    return f"sldprt:configuration:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def FeatureId(NativeId: int) -> str:
    return f"sldprt:feature:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def PlaneId(NativeId: int) -> str:
    return f"sldprt:plane:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def SketchId(NativeId: int) -> str:
    return f"sldprt:sketch:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def ParamId(NativeId: int, NameValue: str) -> str:
    return f"sldprt:parameter:{NativeId}:{NameValue}"


# this definition exists because focused behavior needs one stable owner
def ParamEntries(
    NativeId: int, Dimensions: tuple[NativeDimension, ...]
) -> tuple[tuple[NativeDimension, str], ...]:
    Occurrences: Defaultdict[str, int] = Defaultdict(int)
    Result: list[tuple[NativeDimension, str]] = []
    for Dimension in Dimensions:
        Occurrences[Dimension.name] += 1
        ItemValue = Occurrences[Dimension.name]
        ParamKey = ParamId(NativeId, Dimension.name)
        if ItemValue > 1:
            ParamKey += f":{ItemValue}"
        Result.append((Dimension, ParamKey))
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def SelectionId(
    NativeId: int, LocalId: int, KindValue: str = "edge", ProducerId: int | None = None
) -> str:
    Producer = f":{ProducerId}" if ProducerId is not None else ""
    return f"sldprt:selection:{NativeId}:{KindValue}{Producer}:{LocalId}"


# this definition exists because focused behavior needs one stable owner
def ProfileId(NativeId: int, ProfileIndex: int) -> str:
    return f"sldprt:sketch:{NativeId}:profile:{ProfileIndex}"


# this definition exists because focused behavior needs one stable owner
def ProfileEdgeId(NativeId: int, ProfileIndex: int, EdgeIndex: int) -> str:
    return f"sldprt:sketch:{NativeId}:profile:{ProfileIndex}:edge:{EdgeIndex}"


# this definition exists because focused behavior needs one stable owner
ArcEllipseGeometry = ArcEllipseGeom

# this binding exists because shared behavior needs one stable value
ArcGeometry = ArcGeom

# this binding exists because shared behavior needs one stable value
ArcParabolaGeometry = ArcParabolaGeom


# this binding exists because shared behavior needs one stable value
BooleanOperation = BoolOperation

# this binding exists because shared behavior needs one stable value
BytesIO = BytesIo

# this binding exists because shared behavior needs one stable value
COMPONENT_TREE_STREAM = ComponentTreeStream

# this binding exists because shared behavior needs one stable value
CONTAINER_VERSIONS = ContainerVersions

# this binding exists because shared behavior needs one stable value
CONTENT_TYPES_STREAM = ContentTypesStream

# this binding exists because shared behavior needs one stable value
CadDocument = CadDoc

# this binding exists because shared behavior needs one stable value
CircleGeometry = CircleGeom

# this binding exists because shared behavior needs one stable value
ComponentDocument = ComponentDoc


# this binding exists because shared behavior needs one stable value
ConstraintReference = RuleRef

# this binding exists because shared behavior needs one stable value
DIRECTION_AXIS_ROLE = DirectionAxisRole

# this binding exists because shared behavior needs one stable value
DISPLAY_LISTS_STREAM = DisplayListsStream


# this binding exists because shared behavior needs one stable value
Diagnostic = DiagValue


# this binding exists because shared behavior needs one stable value
EllipseGeometry = EllipseGeom


# this binding exists because shared behavior needs one stable value
FORMAT_ID_BY_SUFFIX = FormatIdBySuffix

# this binding exists because shared behavior needs one stable value
GeometryKind = GeomKind

# this binding exists because shared behavior needs one stable value
INFO = InfoValue

# this binding exists because shared behavior needs one stable value
KEYWORDS_STREAM = KeywordsStream

# this binding exists because shared behavior needs one stable value
KIT_DOCUMENT_STREAM = KitDocStream


# this binding exists because shared behavior needs one stable value
KIT_RESOLVED_STREAM = KitResolvedStream

# this binding exists because shared behavior needs one stable value
LineGeometry = LineGeom

# this binding exists because shared behavior needs one stable value
MATES_STREAM_NAME = MatesStreamName

# this binding exists because shared behavior needs one stable value
MATES_STREAM_SUFFIX = MatesStreamSuffix

# this binding exists because shared behavior needs one stable value
MATE_VALUE_SEMANTICS = MateValueSemantics

# this binding exists because shared behavior needs one stable value
MateConstraint = MateRule


# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ALIGNMENT_BY_CODE = NativeMateAlignmentByCode

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ENTITY_MARKERS = NativeMateEntityMarkers

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_NEUTRAL_KIND_ALIASES = NativeMateNeutralKind

# this binding exists because shared behavior needs one stable value
NativeAssembly = NativeAsm

# this binding exists because shared behavior needs one stable value
NativeAssemblyDefinition = NativeAsmDefinition


# this binding exists because shared behavior needs one stable value
NativeAssemblyOccurrence = NativeAsmItem

# this binding exists because shared behavior needs one stable value
NativeGeometry = NativeGeom


# this binding exists because shared behavior needs one stable value
PLANE_FEATURE_TYPES = PlaneFeatureTypes

# this binding exists because shared behavior needs one stable value
Parameter = Param

# this binding exists because shared behavior needs one stable value
ParameterRole = ParamRole

# this binding exists because shared behavior needs one stable value
ParameterValue = ParamValue

# this binding exists because shared behavior needs one stable value
Path = FilePath

# this binding exists because shared behavior needs one stable value
PathValue = FilePath

# this binding exists because shared behavior needs one stable value
PointGeometry = PointGeom

# this binding exists because shared behavior needs one stable value
RELATIONSHIPS_STREAM = RelationshipsStream

# this binding exists because shared behavior needs one stable value
RESOLVED_FEATURES_STREAM = ResolvedFeaturesStream

# this binding exists because shared behavior needs one stable value
ReferencePlaneFeature = RefPlaneFeature


# this binding exists because shared behavior needs one stable value
SOLID_BODY_FEATURE_TYPES = SolidBodyFeatureTypes

# this binding exists because shared behavior needs one stable value
SUFFIX_BY_FORMAT_ID = SuffixByFormatId

# this binding exists because shared behavior needs one stable value
SelectionPathElement = SelectionPathElem

# this binding exists because shared behavior needs one stable value
SketchConstraint = SketchRule

# this binding exists because shared behavior needs one stable value
SplineGeometry = SplineGeom


# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
build_sldprt = BuildSldprt

# this binding exists because shared behavior needs one stable value
contains_parasolid_payload = ContainsParasolidPayload

# this binding exists because shared behavior needs one stable value
dataclass = DataClass

# this binding exists because shared behavior needs one stable value
decode_brep_model = DecodeBrepModel

# this binding exists because shared behavior needs one stable value
decode_mate_list = DecodeMateList

# this binding exists because shared behavior needs one stable value
decode_native_assembly = DecodeNativeAsm

# this binding exists because shared behavior needs one stable value
decode_native_model = DecodeNativeModel

# this binding exists because shared behavior needs one stable value
decode_partition_stream = DecodePartitionStream

# this binding exists because shared behavior needs one stable value
defaultdict = Defaultdict

# this binding exists because shared behavior needs one stable value
encode_blank_partition_stream = EncodeBlankPartition

# this binding exists because shared behavior needs one stable value
encode_brep_model = EncodeBrepModel


# this binding exists because shared behavior needs one stable value
encode_partition_stream = EncodePartitionStream

# this binding exists because shared behavior needs one stable value
filter_document = FilterDoc

# this binding exists because shared behavior needs one stable value
frozen_mapping = FrozenMapping

# this binding exists because shared behavior needs one stable value
hashlib = Hashlib

# this binding exists because shared behavior needs one stable value
infer_capabilities = InferCapabilities

# this binding exists because shared behavior needs one stable value
is_binary_destination = IsBinaryTarget

# this binding exists because shared behavior needs one stable value
is_native_parasolid_payload = IsNativeParasolidPayload

# this binding exists because shared behavior needs one stable value
json = JsonValue

# this binding exists because shared behavior needs one stable value
math = MathValue

# this binding exists because shared behavior needs one stable value
operation_axis_subelement = OperationAxisSubElem

# this binding exists because shared behavior needs one stable value
os = OsModule

# this binding exists because shared behavior needs one stable value
re = RegexLib

# this binding exists because shared behavior needs one stable value
read_sldprt = ReadSldprt

# this binding exists because shared behavior needs one stable value
replace = Replace

# this binding exists because shared behavior needs one stable value
retained_capabilities = RetainedCapabilities

# this binding exists because shared behavior needs one stable value
semantic_metadata = SemanticMeta

# this binding exists because shared behavior needs one stable value
source_payload_indexes = SourcePayloadIndexes

# this binding exists because shared behavior needs one stable value
struct = Struct

# this binding exists because shared behavior needs one stable value
suppress = Suppress

# this binding exists because shared behavior needs one stable value
tempfile = Tempfile

# this binding exists because shared behavior needs one stable value
with_wrapper_metadata = WithWrapperMeta


# this binding exists because shared behavior needs one stable value
ApplyNative = ApplyNativeMut
