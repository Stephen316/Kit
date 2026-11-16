from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from CmgrInherited import (
    ArchiveFeature,
    CheckArcFeature,
    ReadArcFeature,
    WriteArcFeature,
)
from convert.adapters.solidworks.Container.Archive import (
    KBigObjectTag,
    KClassRefKind,
    KDefinitionKind,
    EncodeNull,
    EncodeString,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter
from convert.adapters.solidworks.Resolved.NamedNode import ReadNamedNode

KNameClass = "moNodeName_c"
KNodeFlags = 0x40000000
KFolders = (
    ("moCommentsFolder_c", "<2i", (0, 0)),
    ("moFavoriteFolder_c", "<4i", (1, 0, 0, 1)),
    ("moHistoryFolder_c", "<2iH", (1, 0, 0)),
    ("moSelectionSetFolder_c", "<2iHi", (1, 0, 0, 1)),
    ("moSensorFolder_c", "<2i", (1, 0)),
    ("moDocsFolder_c", "<2i", (1, 0)),
)


# The model allocates native folder IDs and the caller supplies their saved feature state.
@Dataclass(frozen=True, slots=True)
class SystemFolder:
    Name: str
    TreeId: int
    Feature: ArchiveFeature


# later system objects reuse the name class allocated by the configuration
def ReadFolderName(Cursor: ArchiveCursor) -> tuple[str, int]:
    _ = Cursor.TakePointer((KNameClass,), KClassRefKind, CompactOnly=True)
    return ReadNamedNode(Cursor, (KNodeFlags,))


# framing the names first keeps a failed input from advancing the archive
def PrepFolders(
    Generation: int, Folders: tuple[SystemFolder, ...]
) -> tuple[bytes, ...]:
    RequireArch(Generation, 19000, "resolved standalone folder generation")
    TreeIds = tuple(Folder.TreeId for Folder in Folders)
    RequireArch(
        len(set(TreeIds)) == len(TreeIds)
        and all(type(Id) is int and 0 < Id <= 0x7FFFFFFF for Id in TreeIds),
        True,
        "resolved folder tree identities",
    )
    RequireArch(
        all(Folder.Name and "\0" not in Folder.Name for Folder in Folders),
        True,
        "resolved folder names",
    )
    for Folder in Folders:
        CheckArcFeature(Generation, Folder.Feature)
    return tuple(EncodeString(Folder.Name) for Folder in Folders)


# resolve the inherited class before serializing any new folder definitions
def CheckFolderMap(Writer: ArchiveWriter, Classes: tuple[str, ...], Slots: int) -> None:
    NameClass = Writer.classes.get(KNameClass, 0)
    RequireArch(
        0 < NameClass < Writer.next_index <= KBigObjectTag - Slots
        and all(ClassName not in Writer.classes for ClassName in Classes),
        True,
        "resolved folder allocator",
    )


# the shared node fields precede each subclass's list and feature body
def WriteFolderName(Writer: ArchiveWriter, EncodedName: bytes, TreeId: int) -> None:
    Writer.begin_object(KNameClass, 1)
    Writer.raw(EncodedName)
    Writer.raw(PackFields("<iIii", 0, KNodeFlags, TreeId, 0))
    Writer.string("")
    Writer.i32(0)
    Writer.raw(EncodeNull())


# Folder definitions create slots in sequence and reuse the configuration's name class.
def ReadSysFolders(Cursor: ArchiveCursor, Generation: int) -> tuple[SystemFolder, ...]:
    RequireArch(Generation, 19000, "resolved standalone folder generation")
    Folders = []
    for ClassName, Format, Values in KFolders:
        _ = Cursor.TakePointer((ClassName,), KDefinitionKind, CompactOnly=True)
        Name, TreeId = ReadFolderName(Cursor)
        RequireArch(Cursor.ReadInts("<Hi"), (0, 0), "resolved folder node list")
        Feature = ReadArcFeature(Cursor, Generation)
        RequireArch(Cursor.ReadInts(Format), Values, f"resolved {ClassName} return")
        Folders.append(SystemFolder(Name, TreeId, Feature))
    return tuple(Folders)


# Leave the live namespace at the annotation cabinet's initial allocation.
def WriteSysFolders(
    Writer: ArchiveWriter, Generation: int, Folders: tuple[SystemFolder, ...]
) -> None:
    RequireArch(len(Folders), len(KFolders), "resolved standalone folder count")
    Names = PrepFolders(Generation, Folders)
    CheckFolderMap(
        Writer, tuple(ClassName for ClassName, _, _ in KFolders), 3 * len(KFolders)
    )
    for Folder, Name, (ClassName, Format, Values) in zip(
        Folders, Names, KFolders, strict=True
    ):
        Writer.begin_object(ClassName, 1)
        WriteFolderName(Writer, Name, Folder.TreeId)
        Writer.raw(PackFields("<Hi", 0, 0))
        WriteArcFeature(Writer, Generation, Folder.Feature)
        Writer.raw(PackFields(Format, *Values))
