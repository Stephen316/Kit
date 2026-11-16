from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from PartArchive import PartArchiveWriter
from ResolvedFolders import (
    CheckFolderMap,
    PrepFolders,
    ReadFolderBody,
    SystemFolder,
    WriteFolderBody,
)
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    KObjectRefKind,
    EncodeNull,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor

KBodyFolders = ("moSurfaceBodyFolder_c", "moSolidBodyFolder_c")
KPlainFolders = ("moInkMarkupFolder_c", "moEqnFolder_c")
KMaterialFolder = "moMaterialFolder_c"
KEnvFolder = "moEnvFolder_c"
KCommonWords = (1, 0)
KUnassignedMaterial = 0x80000000


# The environment is a separate root entry between the two groups of definitions.
@Dataclass(frozen=True, slots=True)
class LateFolders:
    Folders: tuple[SystemFolder, ...]
    Environment: int


# The body lists and material assignment must match the guarded ordinary profile.
def ReadLateFolders(Cursor: ArchiveCursor, Generation: int) -> LateFolders:
    RequireArch(Generation, 19000, "resolved later folder generation")
    Folders = []
    for ClassName in KBodyFolders:
        _ = Cursor.TakePointer((ClassName,), KDefinitionKind, CompactOnly=True)
        Folders.append(ReadFolderBody(Cursor, Generation))
        RequireArch(Cursor.ReadInts("<4i"), (*KCommonWords, 0, 0), ClassName)
        Cursor.ReadNull()
        Cursor.ReadNull()
    _, _, Environment = Cursor.TakePointer(
        (KEnvFolder,), KObjectRefKind, CompactOnly=True
    )
    for ClassName in (*KPlainFolders, KMaterialFolder):
        _ = Cursor.TakePointer((ClassName,), KDefinitionKind, CompactOnly=True)
        Folders.append(ReadFolderBody(Cursor, Generation))
        RequireArch(Cursor.ReadInts("<2i"), KCommonWords, ClassName)
    RequireArch(Cursor.ReadText(), "", "resolved material folder name")
    RequireArch(
        Cursor.ReadInts("<I"), (KUnassignedMaterial,), "resolved material folder state"
    )
    return LateFolders(tuple(Folders), Environment)


# The alias reuses the configuration object slot between body and plain folder roots.
def WriteLateFolders(
    Writer: PartArchiveWriter, Generation: int, State: LateFolders
) -> None:
    Classes = (*KBodyFolders, *KPlainFolders, KMaterialFolder)
    RequireArch(len(State.Folders), len(Classes), "resolved later folder count")
    Names = PrepFolders(Generation, State.Folders)
    CheckFolderMap(Writer, Classes, 3 * len(Classes))
    RequireArch(
        type(State.Environment) is int and 0 < State.Environment < Writer.next_index,
        True,
        "resolved environment alias index",
    )
    RequireArch(
        Writer.objects.get(State.Environment), KEnvFolder, "resolved environment alias"
    )
    for ClassName, Folder, Name in zip(Classes, State.Folders, Names, strict=True):
        if ClassName == KPlainFolders[0]:
            Writer.ReferenceObject(State.Environment, KEnvFolder)
        Writer.begin_object(ClassName, 1)
        WriteFolderBody(Writer, Generation, Folder, Name)
        Writer.raw(PackFields("<2i", *KCommonWords))
        if ClassName in KBodyFolders:
            Writer.raw(PackFields("<2i", 0, 0))
            Writer.raw(EncodeNull())
            Writer.raw(EncodeNull())
        elif ClassName == KMaterialFolder:
            Writer.string("")
            Writer.u32(KUnassignedMaterial)
