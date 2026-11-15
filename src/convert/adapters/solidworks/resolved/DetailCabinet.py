from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.FolderNode import FolderNode
from convert.adapters.solidworks.resolved.NamedNode import ReadNamedFeat, ReadNamedNode


# the paired cabinet children refer to each other through the archived note identities
@Dataclass(frozen=True, slots=True)
class NoteIdentity:
    NameValue: str
    FeatureId: int
    ObjectIndex: int


# downstream allocation depends on both cabinet children and their reciprocal links
@Dataclass(frozen=True, slots=True)
class DetailCabinet:
    Cabinet: FolderNode
    Notes: NoteIdentity
    EndTag: NoteIdentity


# each notes object must finish its inherited feature fields before its references
def ReadNotes(Cursor: ArchiveCursor, NotesClass: str, KindValue: str) -> NoteIdentity:
    _, _, ObjectIndex = Cursor.TakePointer((NotesClass,), KindValue, CompactOnly=True)
    _ = Cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    NameValue, FeatureId = ReadNamedFeat(Cursor)
    RequireArch(Cursor.ReadInts("<2i"), (1, 0), "guarded notes folder base")
    return NoteIdentity(NameValue, FeatureId, ObjectIndex)


# the cabinet must reach the same saved notes end tag through its second member
def ReadCabinet(Cursor: ArchiveCursor) -> DetailCabinet:
    Offset = Cursor.Offset
    ClassName = "moDetailCabinet_c"
    _, _, ObjectIndex = Cursor.TakePointer(
        (ClassName,), KDefinitionKind, CompactOnly=True
    )
    _ = Cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    NameValue, FeatureId = ReadNamedNode(Cursor, (0x40000000,))
    RequireArch(Cursor.ReadInts("<H"), (2,), "two resolved cabinet members")
    NotesClass = "moNotesAreaFtrFolder_c"
    Notes = ReadNotes(Cursor, NotesClass, KDefinitionKind)
    EndTag = ReadNotes(Cursor, NotesClass, KClassRefKind)
    _, _, OwnerId = Cursor.TakePointer((NotesClass,), KObjectRefKind, CompactOnly=True)
    RequireArch(OwnerId, Notes.ObjectIndex, "end tag points to notes owner")
    RequireArch(Cursor.ReadInts("<4i"), (0, 0, 1, 1), "guarded end tag trailer")
    RequireArch(Cursor.ReadInts("<4i"), (1, 0, 1, 1), "guarded notes trailer")
    _, _, SavedEnd = Cursor.TakePointer((NotesClass,), KObjectRefKind, CompactOnly=True)
    RequireArch(SavedEnd, EndTag.ObjectIndex, "second cabinet member is its end tag")
    RequireArch(Cursor.ReadInts("<i"), (0,), "guarded cabinet list trailer")
    ReadFeatBase(Cursor.ReadValue, Cursor.ReadPoint, Cursor.ReadNull, Cursor.ReadText)
    TailValue = bytes(12) + b"\xf0\x3f" + bytes(6) + b"\xf0\x3f" + bytes(10)
    RequireArch(Cursor.ReadValue("<32s"), (TailValue,), "guarded cabinet scalar tail")
    return DetailCabinet(
        FolderNode(
            ClassName,
            NameValue,
            FeatureId,
            ObjectIndex,
            Offset,
            Cursor.Offset,
            Cursor.NextIndex,
        ),
        Notes,
        EndTag,
    )
