from typing import TypedDict

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
    ArchiveError,
    ReadTag,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.SavedFileRef import ReadFileRef, SavedFileRef


# trim records must match both the profile allocation and its saved feature identifier
class ProfileOwner(TypedDict):
    profile_object: int
    native_feature_id: int


# trim segments reuse the saved surface document and feature occurrence
class TrimSurface(TypedDict):
    object_index: int
    feature_ref_class: int
    feature_ref_object: int
    file_reference: SavedFileRef
    feature_id: int
    time_word: int
    occurrence: int


# later geometry binding needs the native edge identifier and the trim side class
KContourEdge = TypedDict(
    "KContourEdge", {"object_index": int, "class": str, "edge_id": int}
)

# only these two segment subclasses support the witnessed trim layout
KTrimTypes = ("moSegmLeftTrimEdgeIdRep_c", "moSegmRightTrimEdgeIdRep_c")


# a contour is attached to the resolved profile object rather than its stream position
def CheckTrimOwner(Cursor: ArchiveCursor, Owner: ProfileOwner) -> None:
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moProfileFeature_c",), KObjectRefKind, CompactOnly=True
    )
    RequireArch(
        ObjectIndex, Owner["profile_object"], "trim belongs to the current profile"
    )


# a later contour can reuse only the particular file object allocated earlier
def ReadContourFile(Cursor: ArchiveCursor, ExistingFile: int | None) -> SavedFileRef:
    if ExistingFile is None:
        return ReadFileRef(Cursor)
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moExtObject_c",), KObjectRefKind, CompactOnly=True
    )
    RequireArch(ObjectIndex, ExistingFile, "contour uses the reached file reference")
    return {"object_index": ObjectIndex}


# the first contour surface establishes its native feature and document identity
def ReadTrimSurface(
    Cursor: ArchiveCursor, Owner: ProfileOwner, ExistingFile: int | None = None
) -> TrimSurface:
    KindValue = KDefinitionKind if ExistingFile is None else KClassRefKind
    _, _, Index = Cursor.TakePointer(
        ("moSimpleSurfIdRep_c",), KindValue, CompactOnly=True
    )
    CheckTrimOwner(Cursor, Owner)
    FeatureClass = (
        Cursor.NextIndex
        if ExistingFile is None
        else ReadTag(Cursor.BlobValue, Cursor.Offset).index
    )
    _, _, FeatureRef = Cursor.TakePointer(("moFR_c",), KindValue, CompactOnly=True)
    FileRef = ReadContourFile(Cursor, ExistingFile)
    FeatureId, TimeWord, Occurrence = Cursor.ReadInts("<iIi")
    RequireArch(FeatureId, Owner["native_feature_id"], "contour feature ownership")
    RequireArch(TimeWord < 0xFFFFFFFF, True, "compact contour feature reference time")
    RequireArch(Occurrence, 0, "witnessed first contour occurrence")
    return {
        "object_index": Index,
        "feature_ref_class": FeatureClass,
        "feature_ref_object": FeatureRef,
        "file_reference": FileRef,
        "feature_id": FeatureId,
        "time_word": TimeWord,
        "occurrence": Occurrence,
    }


# each segment must retain the exact file and feature reference of its own surface
def ReadContourEdge(
    Cursor: ArchiveCursor, Owner: ProfileOwner, Surface: TrimSurface
) -> KContourEdge:
    TagValue = ReadTag(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        TagValue.kind in (KDefinitionKind, KClassRefKind), True, "typed trim segment"
    )
    _, ClassName, Index = Cursor.TakePointer(
        KTrimTypes, TagValue.kind, CompactOnly=True
    )
    if ClassName is None:
        raise ArchiveError("Trim segment has no allocated class")
    CheckTrimOwner(Cursor, Owner)
    _ = Cursor.TakePointer(("moFR_c",), KClassRefKind, CompactOnly=True)
    _ = ReadContourFile(Cursor, Surface["file_reference"]["object_index"])
    FeatureId, TimeWord, EdgeId, Extra = Cursor.ReadInts("<iI2i")
    RequireArch(
        (FeatureId, TimeWord, Extra),
        (Surface["feature_id"], Surface["time_word"], 0),
        "same contour document and feature reference",
    )
    return {"object_index": Index, "class": ClassName, "edge_id": EdgeId}
