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


# Both owning streams define the external object and CString handle classes here.
def RequireExtScope(
    Generation: int, NextIndex: int, ClassNames: frozenset[str]
) -> None:
    RequireArch(Generation, 19000, "external file generation")
    RequireArch(
        ClassNames.isdisjoint((KExtObjectClass, KStringHandleClass)),
        True,
        "external file first class definitions",
    )
    RequireArch(
        0 < NextIndex <= KBigObjectTag - 5, True, "external compact allocations"
    )


# A self reference saves flag eight even when its path is empty.
def RequireExtState(State: ExternalFile, SelfReference: bool) -> None:
    RequireArch(
        State.Flags, 8 if SelfReference or State.FilePath else 0, "external file flags"
    )
    RequireArch(0 <= State.SavedTime <= 0xFFFFFFFF, True, "shared file time")
    RequireArch(
        bool(State.Title and State.ConfigName)
        and all(
            "\0" not in Value
            for Value in (State.FilePath, State.Title, State.ConfigName)
        ),
        True,
        "external file text",
    )


# The supported standalone record saves every CString with wide framing.
def ReadExtText(Cursor: ArchiveCursor) -> str:
    RequireArch(
        Cursor.BlobValue.startswith(KStringMarker, Cursor.Offset),
        True,
        "external CString Unicode marker",
    )
    return Cursor.ReadText()


# Both CString handles are separate objects in either enclosing namespace.
def ReadExtRecord(
    Cursor: ArchiveCursor, Generation: int, *, SelfReference: bool
) -> tuple[ExternalFile, int]:
    RequireExtScope(Generation, Cursor.NextIndex, frozenset(Cursor.Classes.values()))
    _ = Cursor.TakePointer((KExtObjectClass,), KDefinitionKind, CompactOnly=True)
    _ = Cursor.TakePointer((KStringHandleClass,), KDefinitionKind, CompactOnly=True)
    FilePath = ReadExtText(Cursor)
    _ = Cursor.TakePointer((KStringHandleClass,), KClassRefKind, CompactOnly=True)
    Title = ReadExtText(Cursor)
    Version, FileState, SavedTime = Cursor.ReadInts(KSharedHeader)
    RequireArch((Version, FileState), (2, 0), "shared file header")
    for _ in range(3):
        RequireArch(ReadExtText(Cursor), "", "shared file optional text")
    SharedEnd, Flags, ExtTime, First, Second, Third = Cursor.ReadInts(KExtFileFields)
    RequireArch(SharedEnd, 0, "shared file return")
    RequireArch(
        (First, Second, Third),
        (1, 0, -1) if SelfReference else (0, 0, 0),
        "external record profile",
    )
    if not SelfReference:
        RequireArch(ExtTime, 0, "configuration manager external time")
    ConfigName = ReadExtText(Cursor)
    RequireArch(Cursor.ReadInts(KConfigReturn), (0, 0, 0, 0), "referenced config")
    State = ExternalFile(FilePath, Title, SavedTime, Flags, ConfigName)
    RequireExtState(State, SelfReference)
    return State, ExtTime


# The shared record ends before the configuration manager or header resumes writing.
def WriteExtRecord(
    Writer: ArchiveWriter,
    Generation: int,
    State: ExternalFile,
    *,
    SelfReference: bool,
    ModifiedTime: int,
) -> None:
    RequireExtScope(Generation, Writer.next_index, frozenset(Writer.classes))
    RequireExtState(State, SelfReference)
    RequireArch(
        0 <= ModifiedTime <= 0xFFFFFFFF if SelfReference else ModifiedTime == 0,
        True,
        "external modification time",
    )
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
    Fields = (1, 0, -1) if SelfReference else (0, 0, 0)
    Writer.raw(PackFields(KExtFileFields, 0, State.Flags, ModifiedTime, *Fields))
    Writer.raw(ConfigBytes)
    Writer.raw(PackFields(KConfigReturn, 0, 0, 0, 0))


# The configuration manager resumes with its own empty map and text fields.
def ReadCmgrExt(Cursor: ArchiveCursor, Generation: int) -> ExternalFile:
    State, _ = ReadExtRecord(Cursor, Generation, SelfReference=False)
    RequireArch(Cursor.ReadInts("<i"), (0,), "CMgr manager external return")
    RequireArch(ReadExtText(Cursor), "", "CMgr manager external name")
    RequireArch(Cursor.ReadInts("<i"), (0,), "CMgr manager external map count")
    return State


# The caller supplies the file metadata and the archive map after the part aliases.
def WriteCmgrExt(Writer: ArchiveWriter, Generation: int, State: ExternalFile) -> None:
    WriteExtRecord(Writer, Generation, State, SelfReference=False, ModifiedTime=0)
    Writer.i32(0)
    Writer.string("")
    Writer.i32(0)
