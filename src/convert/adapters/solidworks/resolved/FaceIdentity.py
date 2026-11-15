from typing import TypedDict

from convert.adapters.solidworks.config.RootLayout import KConfigGen
from convert.adapters.solidworks.container.Archive import KClassRefKind, KObjectRefKind
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor

# saved face identities carry their occurrence and the owning feature and document
SurfaceId = TypedDict(
    "SurfaceId",
    {
        "offset": int,
        "end": int,
        "class": str,
        "object_index": int,
        "feature_ref_object": int,
        "file_ref_object": int,
        "feature_id": int,
        "time_word": int,
        "occurrence": int,
    },
)


# the matching feature reference is inside the typed surface identity
def ReadSurfaceId(
    Cursor: ArchiveCursor,
    ClassName: str,
    Kind: str = KClassRefKind,
    *,
    Cap: bool = False,
) -> SurfaceId:
    Offset = Cursor.Offset
    _, _, Index = Cursor.TakePointer((ClassName,), Kind, CompactOnly=True)
    Cursor.ReadNull()
    _, _, FeatureRef = Cursor.TakePointer(("moFR_c",), KClassRefKind, CompactOnly=True)
    _, _, FileRef = Cursor.TakePointer(
        ("moExtObject_c",), KObjectRefKind, CompactOnly=True
    )
    FeatureId, TimeWord, Occurrence = Cursor.ReadInts("<iIi")
    if Cap:
        RequireArch(Occurrence in (0, 1), True, "recognized end face occurrence")
        RequireArch(Cursor.ReadInts("<i"), (0,), "supported extra end face selector")
    return {
        "offset": Offset,
        "end": Cursor.Offset,
        "class": ClassName,
        "object_index": Index,
        "feature_ref_object": FeatureRef,
        "file_ref_object": FileRef,
        "feature_id": FeatureId,
        "time_word": TimeWord,
        "occurrence": Occurrence,
    }


# the face envelope selects one cap and four rectangle edges before the optional endpoint
class FaceHeader(TypedDict):
    offset: int
    body: int
    object_index: int
    classifier: int


# chooser and component face records share the observed entity envelope
def ReadFaceHead(
    Cursor: ArchiveCursor, Kind: str, ExpectedFlags: int
) -> tuple[FaceHeader, int]:
    Offset = Cursor.Offset
    _, _, Index = Cursor.TakePointer(("moFaceRef_c",), Kind, CompactOnly=True)
    Body = Cursor.Offset
    First, Second, Count = Cursor.ReadInts("<3I")
    RequireArch(
        (First, Second, Count), (1, 0, 6), "witnessed face kind and entity count"
    )
    Flags, Classifier = Cursor.ReadInts("<iI")
    RequireArch(Flags, ExpectedFlags, "witnessed face reference flags")
    _ = Cursor.ReadPoint(2)
    Cursor.ReadNull()
    return {
        "offset": Offset,
        "body": Body,
        "object_index": Index,
        "classifier": Classifier,
    }, Count - 2


# this final empty entity identity remains part of the checked face record
def ReadFaceReturn(Cursor: ArchiveCursor) -> None:
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<5I"),
        (0, 0, KConfigGen, 0, 0),
        "modern face reference trailer",
    )
