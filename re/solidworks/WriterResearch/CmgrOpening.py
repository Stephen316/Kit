from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from CmgrInherited import ReadCmgrFeature, RequireCmgrTime, WriteCmgrFeature
from convert.adapters.solidworks.Container.Archive import KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import (
    KConfigClass,
    KNodeNameClass,
    KRootClass,
    KVisualClass,
    Stamp,
)
from convert.adapters.solidworks.Container.Definition import (
    ArchiveWriter,
    KFirstLoadArrayIndex,
)

# the node constructor sets this bit and the ordinary archive preserves it
KNodeIdFlag = 0x40000000
KFirstConfigurationId = 0


# processed node state is supplied by the caller after native initialization
@Dataclass(frozen=True, slots=True)
class CmgrNodeState:
    UpdateState: int
    SecondaryFlags: int


# the opening carries one named configuration and the manager feature time
@Dataclass(frozen=True, slots=True)
class CmgrOpenFields:
    NameValue: str
    ManagerState: CmgrNodeState
    PartState: CmgrNodeState
    ManagerTime: Stamp


# native configuration ids and archive allocations are separate counters
@Dataclass(frozen=True, slots=True)
class CmgrOpenSlots:
    ConfigId: int
    NextConfigId: int
    PartObject: int
    VisualObject: int


# the bounded constructor requires a clean manager and the checked material path
def RequireOpenFields(Fields: CmgrOpenFields) -> None:
    RequireArch(Fields.NameValue, "Default", "ordinary standalone configuration name")
    RequireArch(
        (Fields.ManagerState, Fields.PartState),
        (CmgrNodeState(0, 0), CmgrNodeState(0, 0x200)),
        "clean node states and completed part material check",
    )


# the lightweight concept owns the node fields and an absent optional object
def WriteCmgrNode(Writer: ArchiveWriter, NodeId: int, State: CmgrNodeState) -> None:
    Writer.raw(
        PackFields(
            "<iIiI", State.UpdateState, KNodeIdFlag, NodeId, State.SecondaryFlags
        )
    )
    Writer.string("")
    Writer.i32(0)


# class definitions consume archive slots while the first part consumes native id zero
def WriteCmgrOpening(
    Writer: ArchiveWriter, Generation: int, Fields: CmgrOpenFields
) -> CmgrOpenSlots:
    RequireCmgrTime(Generation, Fields.ManagerTime)
    RequireOpenFields(Fields)
    RequireArch(
        (Writer.next_index, Writer.classes, Writer.chunks),
        (KFirstLoadArrayIndex, {}, []),
        "fresh standalone CMgr archive",
    )
    Writer.begin_object(KRootClass, 1)
    Writer.u16(0)
    WriteCmgrNode(Writer, -1, Fields.ManagerState)
    Writer.u16(0)
    WriteCmgrFeature(Writer, Generation, Fields.ManagerTime)
    PartObject = Writer.next_index + 1
    Writer.begin_object(KConfigClass, 1)
    Writer.begin_object(KNodeNameClass, 1)
    Writer.string(Fields.NameValue)
    WriteCmgrNode(Writer, KFirstConfigurationId, Fields.PartState)
    VisualObject = Writer.next_index + 1
    Writer.begin_object(KVisualClass, 1)
    return CmgrOpenSlots(
        KFirstConfigurationId, KFirstConfigurationId + 1, PartObject, VisualObject
    )


# signed node state and id remain distinct from the two unsigned flag words
def ReadCmgrNode(Cursor: ArchiveCursor, NodeId: int) -> CmgrNodeState:
    UpdateState, Flags, StoredId, SecondaryFlags = Cursor.ReadInts("<iIiI")
    RequireArch(
        (Flags, StoredId, Cursor.ReadText(), Cursor.ReadInts("<i")),
        (KNodeIdFlag, NodeId, "", (0,)),
        "CMgr node and lightweight concept",
    )
    return CmgrNodeState(UpdateState, SecondaryFlags)


# the typed pointer walk supplies the visual body and its inherited allocation map
def ReadOpenFields(
    BlobValue: bytes, Generation: int
) -> tuple[ArchiveCursor, CmgrOpenFields, CmgrOpenSlots]:
    RequireArch(Generation, 19000, "CMgr opening generation")
    Cursor = ArchiveCursor(BlobValue, 0, KFirstLoadArrayIndex, {}, {})
    _ = Cursor.TakePointer((KRootClass,), KDefinitionKind, CompactOnly=True)
    Cursor.ReadNull()
    ManagerState = ReadCmgrNode(Cursor, -1)
    Cursor.ReadNull()
    ManagerTime = ReadCmgrFeature(Cursor, Generation)
    _, _, PartObject = Cursor.TakePointer(
        (KConfigClass,), KDefinitionKind, CompactOnly=True
    )
    _ = Cursor.TakePointer((KNodeNameClass,), KDefinitionKind, CompactOnly=True)
    NameValue = Cursor.ReadText()
    PartState = ReadCmgrNode(Cursor, KFirstConfigurationId)
    _, _, VisualObject = Cursor.TakePointer(
        (KVisualClass,), KDefinitionKind, CompactOnly=True
    )
    Fields = CmgrOpenFields(NameValue, ManagerState, PartState, ManagerTime)
    RequireOpenFields(Fields)
    return (
        Cursor,
        Fields,
        CmgrOpenSlots(
            KFirstConfigurationId, KFirstConfigurationId + 1, PartObject, VisualObject
        ),
    )


# existing visual readers use the cursor without consuming caller fields
def ReadCmgrOpening(BlobValue: bytes, Generation: int) -> ArchiveCursor:
    Cursor, _, _ = ReadOpenFields(BlobValue, Generation)
    return Cursor
