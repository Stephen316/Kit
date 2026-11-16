from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from CmgrInherited import ReadArcFeature, WriteArcFeature
from ResolvedFolders import (
    CheckFolderMap,
    PrepFolders,
    ReadFolderName,
    SystemFolder,
    WriteFolderName,
)
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
    EncodeObjectRef,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

KCabinetClass = "moDetailCabinet_c"
KNotesClass = "moNotesAreaFtrFolder_c"
KCabinetReturn = "<iH2dH2i"
KCabinetFields = (0, 0, 1.0, 1.0, 0, 0, 0)
KNotesFlags = (1, 0, 1, 1)
KEndFlags = (0, 0, 1, 1)


# Both list members are real nodes and each has its own tree and archive identity.
@Dataclass(frozen=True, slots=True)
class CabinetState:
    Cabinet: SystemFolder
    Notes: SystemFolder
    EndTag: SystemFolder


# The name and common folder fields finish before the sibling pointer.
def ReadNoteBody(
    Cursor: ArchiveCursor, Generation: int, Kind: str
) -> tuple[SystemFolder, int]:
    _, _, Index = Cursor.TakePointer((KNotesClass,), Kind, CompactOnly=True)
    Name, TreeId = ReadFolderName(Cursor)
    RequireArch(Cursor.ReadInts("<Hi"), (0, 0), "resolved notes node list")
    Feature = ReadArcFeature(Cursor, Generation)
    RequireArch(Cursor.ReadInts("<2i"), (1, 0), "resolved notes folder fields")
    return SystemFolder(Name, TreeId, Feature), Index


# The end tag is loaded through notes and reused by the cabinet's second list member.
def ReadCabinetRec(Cursor: ArchiveCursor, Generation: int) -> CabinetState:
    RequireArch(Generation, 19000, "resolved cabinet generation")
    _ = Cursor.TakePointer((KCabinetClass,), KDefinitionKind, CompactOnly=True)
    Name, TreeId = ReadFolderName(Cursor)
    RequireArch(Cursor.ReadInts("<H"), (2,), "resolved cabinet list")
    Notes, NotesId = ReadNoteBody(Cursor, Generation, KDefinitionKind)
    EndTag, EndId = ReadNoteBody(Cursor, Generation, KClassRefKind)
    _, _, Owner = Cursor.TakePointer((KNotesClass,), KObjectRefKind, CompactOnly=True)
    RequireArch(Owner, NotesId, "resolved end tag owner")
    RequireArch(Cursor.ReadInts("<4i"), KEndFlags, "resolved end tag flags")
    RequireArch(Cursor.ReadInts("<4i"), KNotesFlags, "resolved notes flags")
    _, _, Listed = Cursor.TakePointer((KNotesClass,), KObjectRefKind, CompactOnly=True)
    RequireArch(Listed, EndId, "resolved cabinet end tag alias")
    RequireArch(Cursor.ReadInts("<i"), (0,), "resolved cabinet concept tail")
    Feature = ReadArcFeature(Cursor, Generation)
    RequireArch(
        Cursor.ReadValue(KCabinetReturn), KCabinetFields, "resolved cabinet return"
    )
    return CabinetState(SystemFolder(Name, TreeId, Feature), Notes, EndTag)


# Both notes nodes share their class and save their own inherited features.
def WriteNoteBody(
    Writer: ArchiveWriter, Generation: int, Folder: SystemFolder, Name: bytes
) -> None:
    Writer.begin_object(KNotesClass, 1)
    WriteFolderName(Writer, Name, Folder.TreeId)
    Writer.raw(PackFields("<Hi", 0, 0))
    WriteArcFeature(Writer, Generation, Folder.Feature)
    Writer.raw(PackFields("<2i", 1, 0))


# Allocate the nested notes once and refer to their actual object slots.
def WriteCabinetRec(
    Writer: ArchiveWriter, Generation: int, State: CabinetState
) -> None:
    CabinetName, NotesName, EndName = PrepFolders(
        Generation, (State.Cabinet, State.Notes, State.EndTag)
    )
    CheckFolderMap(Writer, (KCabinetClass, KNotesClass), 8)
    Writer.begin_object(KCabinetClass, 1)
    WriteFolderName(Writer, CabinetName, State.Cabinet.TreeId)
    Writer.u16(2)
    NotesId = Writer.next_index + 1
    WriteNoteBody(Writer, Generation, State.Notes, NotesName)
    EndId = Writer.next_index
    WriteNoteBody(Writer, Generation, State.EndTag, EndName)
    Writer.raw(EncodeObjectRef(NotesId))
    Writer.raw(PackFields("<4i", *KEndFlags))
    Writer.raw(PackFields("<4i", *KNotesFlags))
    Writer.raw(EncodeObjectRef(EndId))
    Writer.i32(0)
    WriteArcFeature(Writer, Generation, State.Cabinet.Feature)
    Writer.raw(PackFields(KCabinetReturn, *KCabinetFields))
