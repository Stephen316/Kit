from __future__ import annotations as Annotations
from dataclasses import dataclass as Dataclass, field as Field
from enum import IntEnum
from pathlib import PureWindowsPath
import math as MathValue
import re as RegexLib
import struct as Struct
from types import MappingProxyType
from typing import Iterable, Literal, Mapping, Sequence

import xml.etree.ElementTree as XmlTree  # noqa: DUO107
from convert.adapters.base import ParseUntrusted
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Core.Display import (  # lgtm[py/unused-import]
    NativeDisplayComponent as NativeDisplayComponent,
    NativeTessellationFace as NativeTessellationFace,
    decode_display_lists as DecodeDisplayLists,
    decode_tessellation_faces as DecodeTessellationFaces,
)
from convert.adapters.solidworks.Container.Format import (
    CLASS_MARKER as ClassMarker,
    COMPONENT_TREE_STREAM as ComponentTreeStream,
    DIMENSION_SCALAR_HEADERS as DimensionScalarHeaders,
    DISPLAY_LISTS_STREAM as DisplayListsStream,
    MATES_STREAM_NAME as MatesStreamName,
    MATES_STREAM_SUFFIX as MatesStreamSuffix,
    SERIALIZED_STRING_MARKER as SerializedStringMarker,
    dimension_scalar_value_offset as DimensionScalarValue,
    is_cad_path as IsCadPath,
    is_component_path as IsComponentPath,
)
from convert.adapters.solidworks.Assembly.MateTypeCatalog import (
    BuildMateTypes,
    BuildRefTypes,
    NativeMateType,
    NativeMateTypeA,
)

# this binding exists because shared behavior needs one stable value
KWideText = RegexLib.compile(b"(?:[ -~\\xa1-\\xff]\\x00){4,}")

# this binding exists because shared behavior needs one stable value
KMateAlignmentOffset = 159

# this binding exists because shared behavior needs one stable value
KMateEntityCountOffset = 164


# this definition exists because focused behavior needs one stable owner
class NativeMateCode(IntEnum):
    ANY = 0
    ALIGNED = 1
    ANTI_ALIGNED = 2
    CLOSEST = 3


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMateA:
    code: NativeMateCode
    api_name: str
    kind: str


# this binding exists because shared behavior needs one stable value
KNativeMateTypes = BuildMateTypes()

# this binding exists because shared behavior needs one stable value
KNativeMateTypeExtensions = (
    NativeMateType(None, "BELT", "belt", ("moMateBeltDim_c",), ("beltmate",), "ratio"),
    NativeMateType(
        None, "BELT_GROUP", "group", ("moBeltMateFolder_c",), ("beltmates",)
    ),
    NativeMateType(
        None, "MATE_REFERENCE_GROUP_FOLDER", "group", ("MateReferenceGroupFolder",)
    ),
)

# this binding exists because shared behavior needs one stable value
KNativeMateTypeRecords = (*KNativeMateTypes, *KNativeMateTypeExtensions)


# this definition exists because focused behavior needs one stable owner
def ClassifierMap(
    Records: Iterable[NativeMateType | NativeMateTypeA],
    AttrValue: Literal["class_names", "name_prefixes", "markers"],
) -> Mapping[str, str]:
    Result: dict[str, str] = {}
    for Record in Records:
        if AttrValue == "markers":
            if not isinstance(Record, NativeMateTypeA):
                raise TypeError("marker classifiers require entity type records")
            Values = Record.markers
        else:
            if not isinstance(Record, NativeMateType):
                raise TypeError("mate classifiers require mate type records")
            Values = (
                Record.class_names
                if AttrValue == "class_names"
                else Record.name_prefixes
            )
        for Value in Values:
            KeyValue = Value.casefold()
            Previous = Result.get(KeyValue)
            if Previous is not None and Previous != Record.kind:
                raise RuntimeError(f"conflicting classifier {Value!r}")
            Result[KeyValue] = Record.kind
    return MappingProxyType(Result)


# this binding exists because shared behavior needs one stable value
KMateKindByClass = ClassifierMap(KNativeMateTypeRecords, "class_names")

# this binding exists because shared behavior needs one stable value
KMateKindByName = ClassifierMap(KNativeMateTypeRecords, "name_prefixes")

# this binding exists because shared behavior needs one stable value
KMateValueSemantics = MappingProxyType(
    {
        Record.kind: Record.value_semantic
        for Record in KNativeMateTypeRecords
        if Record.value_semantic
    }
)

# this binding exists because shared behavior needs one stable value
KNativeMateNeutralKind = MappingProxyType(
    {
        Record.kind: Record.neutral_kind
        for Record in KNativeMateTypeRecords
        if Record.neutral_kind
    }
)

# this binding exists because shared behavior needs one stable value
KNativeMateAlignments = (
    NativeMateA(NativeMateCode.ANY, "swMateReferenceAlignment_Any", "unknown"),
    NativeMateA(NativeMateCode.ALIGNED, "swMateReferenceAlignment_Aligned", "aligned"),
    NativeMateA(
        NativeMateCode.ANTI_ALIGNED,
        "swMateReferenceAlignment_AntiAligned",
        "anti_aligned",
    ),
    NativeMateA(NativeMateCode.CLOSEST, "swMateReferenceAlignment_Closest", "closest"),
)

# this binding exists because shared behavior needs one stable value
KNativeMateAlignmentByCoA = {
    int(Record.code): Record for Record in KNativeMateAlignments
}

# this binding exists because shared behavior needs one stable value
KNativeMateEntityGeomTypA = (
    NativeMateTypeA(0, "swMateUnsupported", "native"),
    NativeMateTypeA(1, "swMatePoint", "point"),
    NativeMateTypeA(2, "swMateLine", "line"),
    NativeMateTypeA(3, "swMatePlane", "plane"),
    NativeMateTypeA(4, "swMateCylinder", "cylinder"),
    NativeMateTypeA(5, "swMateCone", "cone"),
    NativeMateTypeA(6, "swMateSphere", "sphere"),
    NativeMateTypeA(7, "swMateCircle", "circle"),
)

# this binding exists because shared behavior needs one stable value
KNativeMateEntityRefTypes = BuildRefTypes()

# this binding exists because shared behavior needs one stable value
KNativeMateEntityType = (
    NativeMateTypeA(None, "SketchEntity", "sketch_entity", ("^",)),
    NativeMateTypeA(
        None, "CoordinateSystem", "coordinate_system", ("coordinatesystem", "coordsys")
    ),
    NativeMateTypeA(None, "Vertex", "vertex", ("vertex",)),
    NativeMateTypeA(None, "Axis", "axis", ("axis",)),
    NativeMateTypeA(None, "Edge", "edge", ("edge",)),
    NativeMateTypeA(None, "Face", "face", ("face", "surfidrep")),
)

# this binding exists because shared behavior needs one stable value
KNativeMateEntityTypeA = (
    KNativeMateEntityType[0],
    *KNativeMateEntityRefTypes,
    *KNativeMateEntityType[1:],
)

# this binding exists because shared behavior needs one stable value
KNativeMateEntityKindBy = ClassifierMap(KNativeMateEntityTypeA, "markers")

# this binding exists because shared behavior needs one stable value
KNativeMateEntityMarkers = tuple(
    (
        (Marker.casefold(), Record.kind)
        for Record in KNativeMateEntityTypeA
        for Marker in Record.markers
    )
)


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeAsmFile:
    object_id: int
    document_type: str
    creation_time: int
    source_path: str


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeAsmA:
    object_id: int
    name: str
    document_type: str
    file_id: int
    source_path: str
    configuration_name: str
    configuration_id: int
    alternate_configuration_name: str
    last_modified_stamp: int
    configuration_flags: int
    bounding_box_m: tuple[float, float, float, float, float, float] | None
    child_occurrence_ids: tuple[int, ...]
    attributes: tuple[tuple[str, str], ...]


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeAsmItem:
    object_id: int
    feature_id: int
    owner_definition_id: int
    definition_id: int
    name: str
    reference_number: int
    component_reference: str
    configuration_name: str
    configuration_id: int
    transform: tuple[float, ...]
    transform_stamp: int
    suppressed: bool
    hidden: bool
    flexible: bool
    virtual: bool
    exclude_from_bom: bool
    zone: bool
    display_mode: int
    display_quality: int
    edges_in_shaded_mode: bool
    order: int
    attributes: tuple[tuple[str, str], ...]


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeAsmConfig:
    object_id: int
    configuration_id: int
    name: str
    reference: str
    model_id: int
    most_recent: bool
    needs_update: bool
    attributes: tuple[tuple[str, str], ...]


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeDisplay:
    object_id: int
    name: str
    configuration_id: int | None
    attributes: tuple[tuple[str, str], ...]


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMateC:
    component_path: str
    persistent_references: tuple[str, ...]
    source_path: str
    configuration_name: str


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMateB:
    name: str
    value: float
    value_offset: int


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMate:
    name: str
    kind: str
    owner_definition_id: int
    order: int
    entities: tuple[NativeMateC, ...]
    record_offset: int
    record_length: int
    class_name: str
    class_token: int | None
    serialized_strings: tuple[str, ...]
    alignment_code: int | None
    dimensions: tuple[NativeMateB, ...]

    # lowercase value access keeps neutral mate metadata statically typed
    @property
    def value_m(self) -> float | None:
        return (
            self.dimensions[0].value
            if self.kind == "distance" and self.dimensions
            else None
        )

    # lowercase offset access keeps source record locations statically typed
    @property
    def value_offset(self) -> int | None:
        return (
            self.dimensions[0].value_offset
            if self.kind == "distance" and self.dimensions
            else None
        )

    # pascal compatibility preserves historical native mate consumers during migration
    @property
    def ValueM(self) -> float | None:
        return self.value_m

    # pascal compatibility preserves historical native mate consumers during migration
    @property
    def ValueOffset(self) -> int | None:
        return self.value_offset


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeMateList:
    native_id: int
    declared_count: int
    owner_definition_id: int
    mates: tuple[NativeMate, ...]
    stream: str


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class MateRecord:
    name: str
    name_end: int
    start: int
    end: int
    class_name: str
    class_token: int | None
    strings: tuple[str, ...]
    alignment_code: int | None
    dimensions: tuple[NativeMateB, ...]


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeItemPath:
    occurrence_id: int
    definition_id: int
    path: str
    depth: int


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeAsm:
    name: str
    root_definition_id: int
    files: tuple[NativeAsmFile, ...]
    definitions: tuple[NativeAsmA, ...]
    occurrences: tuple[NativeAsmItem, ...]
    configurations: tuple[NativeAsmConfig, ...]
    display_states: tuple[NativeDisplay, ...]
    occurrence_paths: tuple[NativeItemPath, ...]
    mate_lists: tuple[NativeMateList, ...]
    display_components: tuple[NativeDisplayComponent, ...]
    application_version: int


# this definition exists because focused behavior needs one stable owner
def DecodeNativeAsm(
    Archive: SldprtArchive, *, IncludeTessellation: bool = False, **LegacyValues: object
) -> NativeAsm:
    IncludeValue = LegacyValues.get("include_tessellation", IncludeTessellation)
    if not isinstance(IncludeValue, bool):
        raise TypeError("include_tessellation must be a boolean")
    IncludeTessellation = IncludeValue
    UnknownValues = set(LegacyValues) - {"include_tessellation"}
    if UnknownValues:
        Unexpected = next(iter(UnknownValues))
        raise TypeError(
            f"DecodeNativeAsm() got an unexpected keyword argument {Unexpected!r}"
        )
    RootValue = XmlRoot(Archive.require(ComponentTreeStream))
    FileValues = Files(RootValue)
    FileById = {ItemValue.object_id: ItemValue for ItemValue in FileValues}
    Definitions, Occurrences = Models(RootValue, FileById)
    ConfigValues = Configurations(RootValue)
    if not ConfigValues:
        raise SldprtFormatError("assembly contains no configuration")
    RootDefinitionId = ConfigValues[0].model_id
    DefinitionById = {ItemValue.object_id: ItemValue for ItemValue in Definitions}
    if RootDefinitionId not in DefinitionById:
        raise SldprtFormatError("assembly configuration references a missing model")
    ItemPaths = ExpandItemPaths(RootDefinitionId, Definitions, Occurrences)
    MateValues = MateLists(Archive, RootDefinitionId)
    DisplayComponents: tuple[NativeDisplayComponent, ...] = ()
    Display = Archive.get(DisplayListsStream)
    if IncludeTessellation and Display:
        DisplayComponents = DecodeDisplayLists(Display)
    return NativeAsm(
        name=DefinitionById[RootDefinitionId].name,
        root_definition_id=RootDefinitionId,
        files=FileValues,
        definitions=Definitions,
        occurrences=Occurrences,
        configurations=ConfigValues,
        display_states=DisplayStates(RootValue),
        occurrence_paths=ItemPaths,
        mate_lists=MateValues,
        display_components=DisplayComponents,
        application_version=Integer(RootValue.attrib.get("swVersion")),
    )


# mate parsing needs one immutable boundary between binary discovery and semantic reconstruction
@Dataclass(frozen=True, slots=True)
class MateParsePlan:
    NativeId: int
    DeclaredCount: int
    Candidates: tuple[tuple[int, str, int], ...]
    Starts: tuple[int, ...]


# header parsing owns all binary bounds so later phases consume complete record locations
def ParseMatePlan(DataValue: bytes, Stream: str) -> MateParsePlan:
    if len(DataValue) < 6:
        raise SldprtFormatError(f"mate stream is truncated: {Stream}")
    NativeId, DeclaredCount = Struct.unpack_from("<IH", DataValue, 0)
    if DeclaredCount == 0 and len(DataValue) == 6:
        return MateParsePlan(NativeId, DeclaredCount, (), ())
    ClassOffset = DataValue.find(ClassMarker, 6)
    if ClassOffset < 0 or ClassOffset + 6 > len(DataValue):
        raise SldprtFormatError(f"mate stream has no class table: {Stream}")
    ClassSize = Struct.unpack_from("<H", DataValue, ClassOffset + 4)[0]
    ClassEnd = ClassOffset + 6 + ClassSize
    if ClassEnd + 5 > len(DataValue):
        raise SldprtFormatError(f"mate class record is truncated: {Stream}")
    ObjectPrefix = DataValue[ClassEnd : ClassEnd + 2]
    NamePrefix = ObjectPrefix + SerializedStringMarker
    Serialized = PrefixedStrings(DataValue, NamePrefix)
    ScalarTokens = {
        Token
        for Offset, _, NameEnd in Serialized
        if DimensionScalarValue(DataValue, NameEnd, len(DataValue)) is not None
        for Token in (ClassRefToken(DataValue, Offset - 2),)
        if Token is not None
    }
    Candidates = [
        ItemValue
        for ItemValue in Serialized
        if DimensionScalarValue(DataValue, ItemValue[2], len(DataValue)) is None
        and ClassRefToken(DataValue, ItemValue[0] - 2) not in ScalarTokens
    ]
    if len(Candidates) != DeclaredCount:
        raise SldprtFormatError(
            f"mate count mismatch in {Stream}: expected {DeclaredCount}, decoded {len(Candidates)}"
        )
    Starts = tuple((MateRecordStart(DataValue, Offset) for Offset, _, _ in Candidates))
    return MateParsePlan(NativeId, DeclaredCount, tuple(Candidates), Starts)


# record decoding remains separate because byte boundaries and class inference change independently
def BuildMateRecs(DataValue: bytes, PlanValue: MateParsePlan) -> tuple[MateRecord, ...]:
    Records: list[MateRecord] = []
    for Order, ((_, NameValue, NameEnd), Start) in enumerate(
        zip(PlanValue.Candidates, PlanValue.Starts)
    ):
        EndValue = (
            PlanValue.Starts[Order + 1]
            if Order + 1 < len(PlanValue.Starts)
            else len(DataValue)
        )
        Strings = RecordStrings(DataValue, Start, EndValue)
        ClassName = InlineClassName(DataValue, Start)
        Records.append(
            MateRecord(
                name=NameValue,
                name_end=NameEnd,
                start=Start,
                end=EndValue,
                class_name=ClassName,
                class_token=None if ClassName else ClassRefToken(DataValue, Start),
                strings=Strings,
                alignment_code=MateAlignmentA(DataValue, EndValue, NameEnd),
                dimensions=MateDimensions(DataValue, Start, EndValue),
            )
        )
    return tuple(Records)


# class inference stays focused because back references depend on all explicit records
def GetMateClasses(
    Records: tuple[MateRecord, ...],
) -> tuple[Mapping[int, str], Mapping[str, set[str]]]:
    TokenKinds = MateTokenKinds(Records)
    ClassesByKind: dict[str, set[str]] = {}
    for Record in Records:
        if not Record.class_name:
            continue
        KindValue = MateKind(Record.name, Record.class_name)
        if KindValue != "native":
            ClassesByKind.setdefault(KindValue, set()).add(Record.class_name)
    return (TokenKinds, ClassesByKind)


# native mate reconstruction consumes inferred classes without revisiting binary parsing state
def MakeNativeMates(
    Records: tuple[MateRecord, ...],
    TokenKinds: Mapping[int, str],
    ClassesByKind: Mapping[str, set[str]],
    OwnerDefinitionId: int,
) -> tuple[NativeMate, ...]:
    Mates: list[NativeMate] = []
    for Order, Record in enumerate(Records):
        if Record.class_name:
            KindValue = MateKind(Record.name, Record.class_name)
            ClassName = Record.class_name
        else:
            ClassToken = Record.class_token
            KindValue = (
                TokenKinds.get(ClassToken, MateKind(Record.name))
                if ClassToken is not None
                else MateKind(Record.name)
            )
            InferredClasses = ClassesByKind.get(KindValue, set())
            ClassName = next(iter(InferredClasses)) if len(InferredClasses) == 1 else ""
        Mates.append(
            NativeMate(
                name=Record.name,
                kind=KindValue,
                owner_definition_id=OwnerDefinitionId,
                order=Order,
                entities=MateEntities(Record.strings),
                record_offset=Record.start,
                record_length=Record.end - Record.start,
                class_name=ClassName,
                class_token=Record.class_token,
                serialized_strings=Record.strings,
                alignment_code=Record.alignment_code,
                dimensions=Record.dimensions,
            )
        )
    return tuple(Mates)


# public mate decoding composes bounds records class inference and immutable output
def DecodeMateList(
    DataValue: bytes, Stream: str = "", OwnerDefinitionId: int = 0
) -> NativeMateList:
    PlanValue = ParseMatePlan(DataValue, Stream)
    Records = BuildMateRecs(DataValue, PlanValue)
    TokenKinds, ClassesByKind = GetMateClasses(Records)
    Mates = MakeNativeMates(Records, TokenKinds, ClassesByKind, OwnerDefinitionId)
    return NativeMateList(
        native_id=PlanValue.NativeId,
        declared_count=PlanValue.DeclaredCount,
        owner_definition_id=OwnerDefinitionId,
        mates=Mates,
        stream=Stream,
    )


# this definition exists because focused behavior needs one stable owner
def MateLists(
    Archive: SldprtArchive, OwnerDefinitionId: int
) -> tuple[NativeMateList, ...]:
    Result: list[NativeMateList] = []
    for Record in Archive.records:
        Named = IsMateStreamNam(Record.name)
        if not Named and (not IsMateStream(Record.data)):
            continue
        try:
            Decoded = DecodeMateList(Record.data, Record.name, OwnerDefinitionId)
        except SldprtFormatError:
            if Named:
                raise
            continue
        Result.append(Decoded)
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def IsMateStreamNam(NameValue: str) -> bool:
    LeafValue = NameValue.replace("\\", "/").rsplit("/", 1)[-1].casefold()
    return LeafValue == MatesStreamName.casefold() or LeafValue.endswith(
        MatesStreamSuffix.casefold()
    )


# this definition exists because focused behavior needs one stable owner
def IsMateStream(DataValue: bytes) -> bool:
    if len(DataValue) < 12 or DataValue[6:10] != ClassMarker:
        return False
    ClassSize = Struct.unpack_from("<H", DataValue, 10)[0]
    ClassEnd = 12 + ClassSize
    if not 1 <= ClassSize <= 128 or ClassEnd + 5 > len(DataValue):
        return False
    ObjectPrefix = Struct.unpack_from("<H", DataValue, ClassEnd)[0]
    return (
        ObjectPrefix & 32768 != 0
        and DataValue[ClassEnd + 2 : ClassEnd + 5] == SerializedStringMarker
    )


# this definition exists because focused behavior needs one stable owner
def ExpandItemPaths(
    RootDefinitionId: int,
    Definitions: Iterable[NativeAssemblyDefinition],
    Occurrences: Iterable[NativeAssemblyOccurrence],
) -> tuple[NativeItemPath, ...]:
    DefinitionById = {ItemValue.object_id: ItemValue for ItemValue in Definitions}
    Children: dict[int, list[NativeAsmItem]] = {}
    for ItemValue in Occurrences:
        Children.setdefault(ItemValue.owner_definition_id, []).append(ItemValue)
    Result: list[NativeItemPath] = []

    # this definition exists because focused behavior needs one stable owner
    def Visit(
        DefinitionId: int, Prefix: str, Depth: int, Stack: frozenset[int]
    ) -> None:
        if DefinitionId in Stack:
            raise SldprtFormatError("cyclic assembly definition hierarchy")
        Owner = DefinitionById[DefinitionId]
        for ItemValue in Children.get(DefinitionId, []):
            Segment = f"{ItemValue.name}-{ItemValue.reference_number}@{Owner.name}"
            PathValue = f"{Prefix}/{Segment}" if Prefix else Segment
            Result.append(
                NativeItemPath(
                    occurrence_id=ItemValue.object_id,
                    definition_id=ItemValue.definition_id,
                    path=PathValue,
                    depth=Depth,
                )
            )
            Target = DefinitionById[ItemValue.definition_id]
            if Target.document_type == "ASSEMBLY":
                Visit(Target.object_id, PathValue, Depth + 1, Stack | {DefinitionId})

    Visit(RootDefinitionId, "", 0, frozenset())
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def XmlRoot(DataValue: bytes) -> XmlTree.Element:
    Marker = DataValue.find(b"<?xml")
    if Marker >= 0:
        DataValue = DataValue[Marker:]
    try:
        return ParseUntrusted(DataValue)
    except XmlTree.ParseError as ErrorInfo:
        raise SldprtFormatError(
            f"invalid assembly component XML: {ErrorInfo}"
        ) from ErrorInfo


# this definition exists because focused behavior needs one stable owner
def LocalName(ElemValue: ET.Element) -> str:
    return ElemValue.tag.rsplit("}", 1)[-1]


# this definition exists because focused behavior needs one stable owner
def Elements(RootValue: ET.Element, NameValue: str) -> tuple[XmlTree.Element, ...]:
    return tuple(
        (
            ItemValue
            for ItemValue in RootValue.iter()
            if LocalName(ItemValue) == NameValue
        )
    )


# this definition exists because focused behavior needs one stable owner
def Files(RootValue: ET.Element) -> tuple[NativeAsmFile, ...]:
    return tuple(
        (
            NativeAsmFile(
                object_id=Integer(ItemValue.attrib.get("id")),
                document_type=ItemValue.attrib.get("swDocType", ""),
                creation_time=Integer(ItemValue.attrib.get("swCreationTime")),
                source_path=ItemValue.attrib.get("swPath", ""),
            )
            for ItemValue in Elements(RootValue, "swFile")
        )
    )


# this definition exists because focused behavior needs one stable owner
def Models(
    RootValue: ET.Element, Files: dict[int, NativeAssemblyFile]
) -> tuple[tuple[NativeAsmA, ...], tuple[NativeAsmItem, ...]]:
    Definitions: list[NativeAsmA] = []
    Occurrences: list[NativeAsmItem] = []
    Order = 0
    for ItemValue in Elements(RootValue, "swModel"):
        FileId = Integer(ItemValue.attrib.get("swFileRef"))
        Source = Files.get(FileId)
        if Source is None:
            raise SldprtFormatError(f"assembly model references missing file {FileId}")
        ChildElements = tuple(
            (Child for Child in ItemValue if LocalName(Child) == "swReference")
        )
        DefinitionId = Integer(ItemValue.attrib.get("id"))
        Definitions.append(
            NativeAsmA(
                object_id=DefinitionId,
                name=ItemValue.attrib.get("swName", ""),
                document_type=Source.document_type,
                file_id=FileId,
                source_path=Source.source_path,
                configuration_name=ItemValue.attrib.get("swConfigurationName", ""),
                configuration_id=Integer(ItemValue.attrib.get("swConfigurationId")),
                alternate_configuration_name=ItemValue.attrib.get(
                    "swConfigurationAlternateName", ""
                ),
                last_modified_stamp=Integer(
                    ItemValue.attrib.get("swLastModifiedStamp")
                ),
                configuration_flags=Integer(
                    ItemValue.attrib.get("swConfigurationFlags")
                ),
                bounding_box_m=BoundingBox(ItemValue.attrib.get("swBoundingBox")),
                child_occurrence_ids=tuple(
                    (Integer(Child.attrib.get("id")) for Child in ChildElements)
                ),
                attributes=tuple(sorted(ItemValue.attrib.items())),
            )
        )
        for Child in ChildElements:
            Transform = FloatTuple(Child.attrib.get("swTransform"), 16)
            Occurrences.append(
                NativeAsmItem(
                    object_id=Integer(Child.attrib.get("id")),
                    feature_id=Integer(Child.attrib.get("swID")),
                    owner_definition_id=DefinitionId,
                    definition_id=Integer(Child.attrib.get("swModelRef")),
                    name=Child.attrib.get("swName", ""),
                    reference_number=Integer(Child.attrib.get("swReferenceNumber"), 1),
                    component_reference=Child.attrib.get("swComponentReference", ""),
                    configuration_name=Child.attrib.get("swConfigurationName", ""),
                    configuration_id=Integer(Child.attrib.get("swConfigurationId")),
                    transform=Transform,
                    transform_stamp=Integer(Child.attrib.get("swTransformStamp")),
                    suppressed=IsYesAction(Child.attrib.get("swSuppressed")),
                    hidden=IsYesAction(Child.attrib.get("swHidden")),
                    flexible=IsYesAction(Child.attrib.get("swFlexible")),
                    virtual=IsYesAction(Child.attrib.get("swIsVirtualComponent")),
                    exclude_from_bom=IsYesAction(Child.attrib.get("swExcludeFromBOM")),
                    zone=IsYesAction(Child.attrib.get("swZone")),
                    display_mode=Integer(Child.attrib.get("swDisplayMode")),
                    display_quality=Integer(Child.attrib.get("swHlrDisplayQuality")),
                    edges_in_shaded_mode=IsYesAction(
                        Child.attrib.get("swEdgesInShadedMode")
                    ),
                    order=Order,
                    attributes=tuple(sorted(Child.attrib.items())),
                )
            )
            Order += 1
    DefinitionIds = {ItemValue.object_id for ItemValue in Definitions}
    for ItemValueA in Occurrences:
        if ItemValueA.definition_id not in DefinitionIds:
            raise SldprtFormatError(
                f"component {ItemValueA.object_id} references missing model {ItemValueA.definition_id}"
            )
    return (tuple(Definitions), tuple(Occurrences))


# this definition exists because focused behavior needs one stable owner
def Configurations(RootValue: ET.Element) -> tuple[NativeAsmConfig, ...]:
    return tuple(
        (
            NativeAsmConfig(
                object_id=Integer(ItemValue.attrib.get("id")),
                configuration_id=Integer(ItemValue.attrib.get("swID")),
                name=ItemValue.attrib.get("swName", ""),
                reference=ItemValue.attrib.get("swReference", ""),
                model_id=Integer(ItemValue.attrib.get("swModelRef")),
                most_recent=IsYesAction(
                    ItemValue.attrib.get("swMostRecentConfiguration")
                ),
                needs_update=IsYesAction(
                    ItemValue.attrib.get("swConfigurationNeedsUpdate")
                ),
                attributes=tuple(sorted(ItemValue.attrib.items())),
            )
            for ItemValue in Elements(RootValue, "swConfiguration")
        )
    )


# this definition exists because focused behavior needs one stable owner
def DisplayStates(RootValue: ET.Element) -> tuple[NativeDisplay, ...]:
    return tuple(
        (
            NativeDisplay(
                object_id=Integer(ItemValue.attrib.get("id")),
                name=ItemValue.attrib.get("swName", ""),
                configuration_id=(
                    Integer(ItemValue.attrib.get("swConfigurationId"))
                    if "swConfigurationId" in ItemValue.attrib
                    else None
                ),
                attributes=tuple(sorted(ItemValue.attrib.items())),
            )
            for ItemValue in Elements(RootValue, "swDisplayState")
        )
    )


# this definition exists because focused behavior needs one stable owner
def PrefixedStrings(
    DataValue: bytes, Prefix: bytes
) -> tuple[tuple[int, str, int], ...]:
    Result: list[tuple[int, str, int]] = []
    Cursor = 0
    while True:
        Offset = DataValue.find(Prefix, Cursor)
        if Offset < 0:
            break
        Cursor = Offset + 1
        LengthOffset = Offset + len(Prefix)
        Decoded = UtfOneSixString(DataValue, LengthOffset)
        if Decoded is not None:
            Value, EndValue = Decoded
            Result.append((Offset, Value, EndValue))
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def SerializedA(
    DataValue: bytes, Start: int = 0, EndValue: int | None = None
) -> tuple[tuple[int, str, int], ...]:
    Limit = len(DataValue) if EndValue is None else min(EndValue, len(DataValue))
    Result: list[tuple[int, str, int]] = []
    Cursor = max(Start, 0)
    while True:
        Offset = DataValue.find(SerializedStringMarker, Cursor, Limit)
        if Offset < 0:
            break
        Cursor = Offset + 1
        Decoded = UtfOneSixString(
            DataValue, Offset + len(SerializedStringMarker), Limit
        )
        if Decoded is not None:
            Value, StringEnd = Decoded
            Result.append((Offset, Value, StringEnd))
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def UtfOneSixString(
    DataValue: bytes, LengthOffset: int, EndValue: int | None = None
) -> tuple[str, int] | None:
    Limit = len(DataValue) if EndValue is None else EndValue
    if LengthOffset >= Limit:
        return None
    Length = DataValue[LengthOffset]
    if Length == 255:
        return None
    StringStart = LengthOffset + 1
    StringEnd = StringStart + Length * 2
    if StringEnd > Limit:
        return None
    try:
        Value = DataValue[StringStart:StringEnd].decode("utf-16le")
    except UnicodeDecodeError:
        return None
    if any((ord(Character) < 32 for Character in Value)):
        return None
    return (Value, StringEnd)


# this definition exists because focused behavior needs one stable owner
def MateRecordStart(DataValue: bytes, NamePrefixOffset: int) -> int:
    Inline = DataValue.rfind(ClassMarker, 0, NamePrefixOffset)
    if Inline >= 0 and Inline + 6 <= NamePrefixOffset:
        SizeValue = Struct.unpack_from("<H", DataValue, Inline + 4)[0]
        if Inline + 6 + SizeValue in (NamePrefixOffset - 2, NamePrefixOffset):
            return Inline
    return max(6, NamePrefixOffset - 2)


# this definition exists because focused behavior needs one stable owner
def InlineClassName(DataValue: bytes, Start: int) -> str:
    if DataValue[Start : Start + 4] != ClassMarker:
        return ""
    if Start + 6 > len(DataValue):
        return ""
    SizeValue = Struct.unpack_from("<H", DataValue, Start + 4)[0]
    try:
        return DataValue[Start + 6 : Start + 6 + SizeValue].decode("ascii")
    except UnicodeDecodeError:
        return ""


# this definition exists because focused behavior needs one stable owner
def ClassRefToken(DataValue: bytes, Offset: int) -> int | None:
    if Offset < 0 or Offset + 2 > len(DataValue):
        return None
    Token = Struct.unpack_from("<H", DataValue, Offset)[0]
    return Token if Token & 32768 and Token != 65535 else None


# this definition exists because focused behavior needs one stable owner
def MateTokenKinds(Records: Sequence[MateRecord]) -> dict[int, str]:
    Candidates: dict[int, set[str]] = {}
    for Record in Records:
        ClassToken = Record.class_token
        if Record.class_name or ClassToken is None:
            continue
        KindValue = MateKind(Record.name)
        if KindValue != "native":
            Candidates.setdefault(ClassToken, set()).add(KindValue)
    return {
        Token: next(iter(Kinds))
        for Token, Kinds in Candidates.items()
        if len(Kinds) == 1
    }


# this definition exists because focused behavior needs one stable owner
def MateEntities(Strings: tuple[str, ...]) -> tuple[NativeMateC, ...]:
    SourcePaths = tuple((Value for Value in Strings if IsCadPath(Value)))
    EntityValues: list[tuple[str, list[str]]] = []
    Persistent: list[str] = []
    for Value in Strings:
        if "^" in Value and "@" in Value:
            continue
        if Value.casefold().startswith("mo"):
            Persistent.append(Value)
            continue
        if IsComponentPath(Value):
            EntityValues.append((Value, Persistent))
            Persistent = []
            continue
        if "@" in Value and EntityValues:
            EntityValues[-1][1].append(Value)
            continue
        if "@" in Value:
            Persistent.append(Value)
    Entities: list[NativeMateC] = []
    for ComponentPath, References in EntityValues:
        LeafValue = ComponentPath.rsplit("/", 1)[-1].split("@", 1)[0]
        SourceName = RegexLib.sub("-\\d+$", "", LeafValue).casefold()
        SourcePath = next(
            (
                Value
                for Value in SourcePaths
                if PureWindowsPath(Value).stem.casefold() == SourceName
            ),
            "",
        )
        Entities.append(
            NativeMateC(
                component_path=ComponentPath,
                persistent_references=tuple(References),
                source_path=SourcePath,
                configuration_name="",
            )
        )
    Synthetic = tuple((Value for Value in Strings if "^" in Value and "@" in Value))
    Entities.extend(
        (
            NativeMateC(
                component_path="",
                persistent_references=(Value,),
                source_path="",
                configuration_name="",
            )
            for Value in Synthetic
        )
    )
    if Persistent:
        Entities.append(NativeMateC("", tuple(Persistent), "", ""))
    return tuple(Entities)


# this definition exists because focused behavior needs one stable owner
def MateKind(NameValue: str, ClassName: str = "") -> str:
    NormalizedClass = ClassName.casefold().strip()
    if NormalizedClass:
        return KMateKindByClass.get(NormalizedClass, "native")
    Lowered = NameValue.casefold().strip()
    Match = RegexLib.fullmatch("([a-z]+)(\\d+)(?:___endtag___)?", Lowered)
    return KMateKindByName.get(Match.group(1), "native") if Match else "native"


# this definition exists because focused behavior needs one stable owner
def MateAlignmentA(DataValue: bytes, EndValue: int, NameEnd: int) -> int | None:
    AlignmentOffset = NameEnd + KMateAlignmentOffset
    EntityCountOffset = NameEnd + KMateEntityCountOffset
    if EntityCountOffset + 4 > EndValue:
        return None
    EntityCount = Struct.unpack_from("<I", DataValue, EntityCountOffset)[0]
    if EntityCount != 2:
        return None
    try:
        AlignmentCode = Struct.unpack_from("<H", DataValue, AlignmentOffset)[0]
    except Struct.error:
        return None
    return AlignmentCode if AlignmentCode in KNativeMateAlignmentByCoA else None


# this definition exists because focused behavior needs one stable owner
def MateDimensions(
    DataValue: bytes, Start: int, EndValue: int
) -> tuple[NativeMateB, ...]:
    Result: list[NativeMateB] = []
    for _, NameValue, StringEnd in SerializedA(DataValue, Start, EndValue):
        ValueOffset = DimensionScalarValue(DataValue, StringEnd, EndValue)
        if ValueOffset is None:
            continue
        Value = Struct.unpack_from("<d", DataValue, ValueOffset)[0]
        if MathValue.isfinite(Value):
            Result.append(NativeMateB(NameValue, Value, ValueOffset))
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def RecordStrings(DataValue: bytes, Start: int, EndValue: int) -> tuple[str, ...]:
    Values = [
        (Offset, Value)
        for Offset, Value, _ in SerializedA(DataValue, Start, EndValue)
        if Value
    ]
    for Match in KWideText.finditer(DataValue, Start, EndValue):
        Values.append((Match.start(), Match.group().decode("utf-16le")))

    # this callback exists because local behavior needs one focused transformation
    Values.sort(key=lambda ItemValue: ItemValue[0])
    Result: list[str] = []
    for _, Value in Values:
        if not Result or Result[-1] != Value:
            Result.append(Value)
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def BoundingBox(
    Value: str | None,
) -> tuple[float, float, float, float, float, float] | None:
    if not Value:
        return None
    Result = FloatTuple(Value, 6)
    return (Result[0], Result[1], Result[2], Result[3], Result[4], Result[5])


# this definition exists because focused behavior needs one stable owner
def FloatTuple(Value: str | None, Count: int) -> tuple[float, ...]:
    if Value is None:
        raise SldprtFormatError("required floating-point tuple is missing")
    Result = tuple((float(ItemValue) for ItemValue in Value.split()))
    if len(Result) != Count or not all(
        (MathValue.isfinite(ItemValue) for ItemValue in Result)
    ):
        raise SldprtFormatError(
            f"expected {Count} finite floating-point values, found {len(Result)}"
        )
    return Result


# this definition exists because focused behavior needs one stable owner
def Integer(Value: str | None, Default: int = 0) -> int:
    try:
        return int(Value) if Value is not None else Default
    except ValueError as ErrorInfo:
        raise SldprtFormatError(f"invalid integer value {Value!r}") from ErrorInfo


# this definition exists because focused behavior needs one stable owner
def IsYesAction(Value: str | None) -> bool:
    return Value == "YES"


# this binding exists because shared behavior needs one stable value
CLASS_MARKER = ClassMarker

# this binding exists because shared behavior needs one stable value
COMPONENT_TREE_STREAM = ComponentTreeStream


# this binding exists because shared behavior needs one stable value
DIMENSION_SCALAR_HEADERS = DimensionScalarHeaders

# this binding exists because shared behavior needs one stable value
DISPLAY_LISTS_STREAM = DisplayListsStream

# this binding exists because shared behavior needs one stable value
ET = XmlTree

# this binding exists because shared behavior needs one stable value
MATES_STREAM_NAME = MatesStreamName

# this binding exists because shared behavior needs one stable value
MATES_STREAM_SUFFIX = MatesStreamSuffix


# this binding exists because shared behavior needs one stable value
MATE_VALUE_SEMANTICS = KMateValueSemantics


# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ALIGNMENTS = KNativeMateAlignments

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ALIGNMENT_BY_CODE = KNativeMateAlignmentByCoA

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ENTITY_GEOMETRY_TYPES = KNativeMateEntityGeomTypA

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ENTITY_KIND_BY_MARKER = KNativeMateEntityKindBy

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ENTITY_MARKERS = KNativeMateEntityMarkers

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ENTITY_REFERENCE_TYPES = KNativeMateEntityRefTypes

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ENTITY_TYPE_EXTENSIONS = KNativeMateEntityType

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ENTITY_TYPE_RECORDS = KNativeMateEntityTypeA

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_NEUTRAL_KIND_ALIASES = KNativeMateNeutralKind

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_TYPES = KNativeMateTypes

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_TYPE_EXTENSIONS = KNativeMateTypeExtensions

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_TYPE_RECORDS = KNativeMateTypeRecords

# this binding exists because shared behavior needs one stable value
NativeAssembly = NativeAsm

# this binding exists because shared behavior needs one stable value
NativeAssemblyConfiguration = NativeAsmConfig

# this binding exists because shared behavior needs one stable value
NativeAssemblyDefinition = NativeAsmA


# this binding exists because shared behavior needs one stable value
NativeAssemblyFile = NativeAsmFile

# this binding exists because shared behavior needs one stable value
NativeAssemblyOccurrence = NativeAsmItem

# this binding exists because shared behavior needs one stable value
NativeDisplayState = NativeDisplay

# this binding exists because shared behavior needs one stable value
NativeMateAlignment = NativeMateA

# this binding exists because shared behavior needs one stable value
NativeMateAlignmentCode = NativeMateCode

# this binding exists because shared behavior needs one stable value
NativeMateDimension = NativeMateB

# this binding exists because shared behavior needs one stable value
NativeMateEntity = NativeMateC

# this binding exists because shared behavior needs one stable value
NativeMateEntityType = NativeMateTypeA


# this binding exists because shared behavior needs one stable value
NativeOccurrencePath = NativeItemPath

# this binding exists because shared behavior needs one stable value
SERIALIZED_STRING_MARKER = SerializedStringMarker

# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
dataclass = Dataclass

# this binding exists because shared behavior needs one stable value
decode_display_lists = DecodeDisplayLists

# this binding exists because shared behavior needs one stable value
decode_mate_list = DecodeMateList

# this binding exists because shared behavior needs one stable value
decode_native_assembly = DecodeNativeAsm

# this binding exists because shared behavior needs one stable value
decode_tessellation_faces = DecodeTessellationFaces

# this binding exists because shared behavior needs one stable value
dimension_scalar_value_offset = DimensionScalarValue


# this binding exists because shared behavior needs one stable value
expand_occurrence_paths = ExpandItemPaths

# this binding exists because shared behavior needs one stable value
field = Field

# this binding exists because shared behavior needs one stable value
is_cad_path = IsCadPath

# this binding exists because shared behavior needs one stable value
is_component_path = IsComponentPath

# this binding exists because shared behavior needs one stable value
math = MathValue

# this binding exists because shared behavior needs one stable value
re = RegexLib

# this binding exists because shared behavior needs one stable value
struct = Struct


# this binding exists because shared behavior needs one stable value
MateStream = IsMateStream

# this binding exists because shared behavior needs one stable value
MateStreamName = IsMateStreamNam


# this binding exists because shared behavior needs one stable value
YesAction = IsYesAction
