"""The generation-19000 custom property manager for an ordinary unadorned part."""

from dataclasses import dataclass

from PartFraming import VersionStorage
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    EncodeNull,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import (
    ArchiveWriter,
    KFirstLoadArrayIndex,
)


CUSTOM_PROPERTIES = "Contents/CusProps"
MANAGER_CLASS = "moCusPropMgr_c"
CONTAINER_CLASS = "moCusPropContainer_c"
FILE_CLASS = "moFilePropContainer_c"
CUT_LIST_CLASS = "moCutListPropContainer_c"
DEFAULT_MANAGER_SENTINEL = -1
MODERN_PROPERTY_ARCHITECTURE = 1
CONTAINER_INITIAL_STATE = 0


@dataclass(frozen=True)
class PartPropertyInventory:
    ContainerKey: int
    FilePropertyCount: int
    GlobalCutListGroupCount: int
    ConfiguredCutListGroupCount: int
    HasWeldmentContainer: bool
    CopyAndLinkToRepresentations: bool


# The fixed profile keeps the file and cut-list containers with no property entries.
def EncodePartProperties(Generation: int, State: PartPropertyInventory) -> bytes:
    VersionStorage(Generation)
    Counts = (
        State.FilePropertyCount,
        State.GlobalCutListGroupCount,
        State.ConfiguredCutListGroupCount,
    )
    RequireArch(
        (type(State.ContainerKey), State.ContainerKey),
        (int, 0),
        "standalone property container key",
    )
    RequireArch(
        all(type(Count) is int and Count == 0 for Count in Counts),
        True,
        "empty native file and cut-list property inventories",
    )
    RequireArch(
        (
            State.HasWeldmentContainer is False,
            State.CopyAndLinkToRepresentations is False,
        ),
        (True, True),
        "standalone part without weldment properties or representation links",
    )
    Writer = ArchiveWriter()
    Writer.BeginObject(MANAGER_CLASS, 1)
    Writer.i32(DEFAULT_MANAGER_SENTINEL)
    Writer.i32(MODERN_PROPERTY_ARCHITECTURE)
    Writer.i32(1)
    Writer.i32(State.ContainerKey)
    Writer.BeginObject(CONTAINER_CLASS, 1)
    Writer.BeginObject(FILE_CLASS, 1)
    Writer.raw(EncodeNull())
    Writer.raw(EncodeNull())
    Writer.BeginObject(CUT_LIST_CLASS, 1)
    Writer.i32(State.GlobalCutListGroupCount)
    Writer.i32(State.ConfiguredCutListGroupCount)
    Writer.raw(EncodeNull())
    Writer.i32(CONTAINER_INITIAL_STATE)
    Writer.u8(int(State.CopyAndLinkToRepresentations))
    return Writer.build()


# Consume every native field and resolve all owned class and object slots.
def ReadPartProperties(Generation: int, Data: bytes) -> PartPropertyInventory:
    VersionStorage(Generation)
    Cursor = ArchiveCursor(Data, 0, KFirstLoadArrayIndex, {}, {})
    _ = Cursor.TakePointer((MANAGER_CLASS,), KDefinitionKind, CompactOnly=True)
    RequireArch(
        Cursor.ReadInts("<iii"),
        (DEFAULT_MANAGER_SENTINEL, MODERN_PROPERTY_ARCHITECTURE, 1),
        "ordinary part property manager and one keyed container",
    )
    (Key,) = Cursor.ReadInts("<i")
    RequireArch(Key, 0, "standalone property container key")
    _ = Cursor.TakePointer((CONTAINER_CLASS,), KDefinitionKind, CompactOnly=True)
    _ = Cursor.TakePointer((FILE_CLASS,), KDefinitionKind, CompactOnly=True)
    Cursor.ReadNull()
    Cursor.ReadNull()
    _ = Cursor.TakePointer((CUT_LIST_CLASS,), KDefinitionKind, CompactOnly=True)
    GlobalCount, ConfiguredCount = Cursor.ReadInts("<ii")
    RequireArch((GlobalCount, ConfiguredCount), (0, 0), "empty cut-list property maps")
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<iB"),
        (CONTAINER_INITIAL_STATE, 0),
        "property container initial state and representation link flag",
    )
    RequireArch(Cursor.Offset, len(Data), "complete native custom property stream")
    return PartPropertyInventory(Key, 0, GlobalCount, ConfiguredCount, False, False)
