from typing import NotRequired, TypedDict

from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor


# later contour records need the same saved file slot without exposing its path
class SavedFileRef(TypedDict):
    object_index: int
    offset: NotRequired[int]
    end: NotRequired[int]
    shared_time_word: NotRequired[int]


# a local document reference materializes its framed filename handles in the same map
def ReadFileRef(Cursor: ArchiveCursor) -> SavedFileRef:
    Offset = Cursor.Offset
    _, _, Index = Cursor.TakePointer(
        ("moExtObject_c",), KDefinitionKind, CompactOnly=True
    )
    _ = Cursor.TakePointer(("moCStringHandle_c",), KDefinitionKind, CompactOnly=True)
    _ = Cursor.ReadText()
    _ = Cursor.TakePointer(("moCStringHandle_c",), KClassRefKind, CompactOnly=True)
    RequireArch(bool(Cursor.ReadText()), True, "saved local document name present")
    ObjKind, SharedFlags, SharedTime = Cursor.ReadInts("<HBI")
    RequireArch((ObjKind, SharedFlags), (2, 0), "saved part file identity")
    RequireArch(
        [Cursor.ReadText() for _ in range(3)], [""] * 3, "empty alternate names"
    )
    RequireArch(Cursor.ReadInts("<B"), (0,), "guarded shared file state")
    FileFlags, _ = Cursor.ReadInts("<BI")
    RequireArch(FileFlags in (0, 8), True, "guarded external reference state")
    RequireArch(Cursor.ReadInts("<3i"), (0, 0, 0), "guarded local file scalars")
    RequireArch(Cursor.ReadText(), "Default", "saved local configuration name")
    RequireArch(
        Cursor.ReadInts("<2iIi"), (0, 0, 0, 0), "guarded file reference trailer"
    )
    return {
        "offset": Offset,
        "object_index": Index,
        "end": Cursor.Offset,
        "shared_time_word": SharedTime,
    }
