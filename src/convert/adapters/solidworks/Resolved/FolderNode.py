from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    KArchiveScalar,
)
from convert.adapters.solidworks.Resolved.NamedNode import ReadNamedFeat


# resolved folder scopes must preserve both feature and archive identities
@Dataclass(frozen=True, slots=True)
class FolderNode:
    ClassName: str
    NameValue: str
    FeatureId: int
    ObjectIndex: int
    Offset: int
    EndOffset: int
    NextIndex: int


# loading the saved folder through its own fields keeps the next object boundary exact
def ReadFolder(
    Cursor: ArchiveCursor,
    ClassName: str,
    SuffixFormat: str,
    SuffixValue: tuple[KArchiveScalar, ...],
    NullCount: int = 0,
) -> FolderNode:
    Offset = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(
        (ClassName,), KDefinitionKind, CompactOnly=True
    )
    _ = Cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    NameValue, FeatureId = ReadNamedFeat(Cursor)
    RequireArch(
        Cursor.ReadValue(SuffixFormat), SuffixValue, f"guarded {ClassName} suffix"
    )
    for _ in range(NullCount):
        Cursor.ReadNull()
    return FolderNode(
        ClassName,
        NameValue,
        FeatureId,
        ObjectIndex,
        Offset,
        Cursor.Offset,
        Cursor.NextIndex,
    )
