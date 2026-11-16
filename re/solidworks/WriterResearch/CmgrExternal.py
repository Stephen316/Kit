from dataclasses import dataclass as DataClass
from struct import pack as PackFields

from convert.adapters.solidworks.Container.Archive import (
    KBigObjectTag,
    KClassRefKind,
    KDefinitionKind,
    KStringMarker,
    EncodeString,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import (
    KExtObjectClass,
    KStringHandleClass,
)
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

KSharedHeader = "<HBI"
KExtFileFields = "<BBI3i"
KConfigReturn = "<iiIi"


# Named fields separate caller file metadata from the fixed standalone archive fields.
@DataClass(frozen=True, slots=True)
class ExternalFile:
    FilePath: str
    Title: str
    SavedTime: int
    Flags: int
    ConfigName: str


# This profile covers the first external object of a standalone configuration manager.
def RequireExtScope(
    Generation: int, NextIndex: int, ClassNames: frozenset[str]
) -> None:
    RequireArch(Generation, 19000, "CMgr external file generation")
    RequireArch(
        ClassNames.isdisjoint((KExtObjectClass, KStringHandleClass)),
        True,
        "CMgr external file first class definitions",
    )
    RequireArch(
        0 < NextIndex <= KBigObjectTag - 5, True, "CMgr external compact allocations"
    )


# The path and flag combinations are restricted to the two observed save forms.
def RequireExtState(State: ExternalFile) -> None:
    RequireArch(State.Flags, 8 if State.FilePath else 0, "CMgr external file flags")
    RequireArch(0 <= State.SavedTime <= 0xFFFFFFFF, True, "CMgr shared file time")
    RequireArch(
        bool(State.Title and State.ConfigName)
        and all(
            "\0" not in Value
            for Value in (State.FilePath, State.Title, State.ConfigName)
        ),
        True,
        "CMgr external file text",
    )


# The supported standalone record saves every CString with wide framing.
def ReadExtText(Cursor: ArchiveCursor) -> str:
    RequireArch(
        Cursor.BlobValue.startswith(KStringMarker, Cursor.Offset),
        True,
        "CMgr external CString Unicode marker",
    )
    return Cursor.ReadText()


# Both CString handles are separate objects in the enclosing archive namespace.
def ReadCmgrExt(Cursor: ArchiveCursor, Generation: int) -> ExternalFile:
    RequireExtScope(Generation, Cursor.NextIndex, frozenset(Cursor.Classes.values()))
    _ = Cursor.TakePointer((KExtObjectClass,), KDefinitionKind, CompactOnly=True)
    _ = Cursor.TakePointer((KStringHandleClass,), KDefinitionKind, CompactOnly=True)
    FilePath = ReadExtText(Cursor)
    _ = Cursor.TakePointer((KStringHandleClass,), KClassRefKind, CompactOnly=True)
    Title = ReadExtText(Cursor)
    Version, FileState, SavedTime = Cursor.ReadInts(KSharedHeader)
    RequireArch((Version, FileState), (2, 0), "CMgr shared file header")
    for _ in range(3):
        RequireArch(ReadExtText(Cursor), "", "CMgr shared file optional text")
    SharedEnd, Flags, ExtTime, First, Second, Third = Cursor.ReadInts(KExtFileFields)
    RequireArch(
        (SharedEnd, ExtTime, First, Second, Third),
        (0, 0, 0, 0, 0),
        "CMgr external fields",
    )
    ConfigName = ReadExtText(Cursor)
    RequireArch(Cursor.ReadInts(KConfigReturn), (0, 0, 0, 0), "CMgr referenced config")
    RequireArch(Cursor.ReadInts("<i"), (0,), "CMgr manager external return")
    RequireArch(ReadExtText(Cursor), "", "CMgr manager external name")
    RequireArch(Cursor.ReadInts("<i"), (0,), "CMgr manager external map count")
    State = ExternalFile(FilePath, Title, SavedTime, Flags, ConfigName)
    RequireExtState(State)
    return State


# The caller supplies the file metadata and the archive map after the part aliases.
def WriteCmgrExt(Writer: ArchiveWriter, Generation: int, State: ExternalFile) -> None:
    RequireExtScope(Generation, Writer.next_index, frozenset(Writer.classes))
    RequireExtState(State)
    PathBytes = EncodeString(State.FilePath)
    TitleBytes = EncodeString(State.Title)
    ConfigBytes = EncodeString(State.ConfigName)
    Writer.begin_object(KExtObjectClass, 1)
    Writer.begin_object(KStringHandleClass, 1)
    Writer.raw(PathBytes)
    Writer.begin_object(KStringHandleClass, 1)
    Writer.raw(TitleBytes)
    Writer.raw(PackFields(KSharedHeader, 2, 0, State.SavedTime))
    for _ in range(3):
        Writer.string("")
    Writer.raw(PackFields(KExtFileFields, 0, State.Flags, 0, 0, 0, 0))
    Writer.raw(ConfigBytes)
    Writer.raw(PackFields(KConfigReturn, 0, 0, 0, 0))
    Writer.i32(0)
    Writer.string("")
    Writer.i32(0)
