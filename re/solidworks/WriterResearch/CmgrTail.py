from struct import pack as PackFields

from convert.adapters.solidworks.Container.Archive import (
    KBigObjectTag,
    KClassRefKind,
    KDefinitionKind,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import (
    KObjectListClass as KListClass,
    FeatureStamp,
    Stamp,
)
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# the intervening manager stores an empty keyed map and four scalar words
KManagerWords = (0, 0, 1, 0, 0)

# the second list precedes empty maps, a vector, a string array, and a plane selector
KCollectionFormat = "<H5iHiIi"
KCollectionWords = (0, 0, 0, 0, 0, 0, 0, 0, 2, 0)

# the absent last edit time is followed by empty maps and the modern presence word
KLastEditFormat = "<3iI2iI"
KLastEditWords = (0, 0, 0, 0xFFFFFFFF, 0, 0, 0)


# typed stamps must fit the saved signed tree ID and the two unsigned time words
def RequireStamps(Stamps: tuple[FeatureStamp, ...]) -> None:
    TreeIds = {Entry.tree_id for Entry in Stamps}
    RequireArch(len(TreeIds) == len(Stamps) <= 2, True, "CMgr feature stamp count")
    RequireArch(
        all(
            0 < Entry.tree_id <= 0x7FFFFFFF
            and 0 <= Entry.stamp.high <= 0xFFFFFFFF
            and 0 <= Entry.stamp.low <= 0xFFFFFFFF
            for Entry in Stamps
        ),
        True,
        "CMgr feature stamp fields",
    )


# the caller owns the current archive namespace and supplies the active feature stamps
def WriteCmgrTail(
    Writer: ArchiveWriter, Generation: int, Stamps: tuple[FeatureStamp, ...]
) -> None:
    RequireArch(Generation, 19000, "modern CMgr tail generation")
    RequireStamps(Stamps)
    RequireArch(KListClass in Writer.classes, False, "first CMgr list class")
    RequireArch(0 < Writer.next_index < KBigObjectTag, True, "compact CMgr list class")
    Writer.begin_object(KListClass, 1)
    Writer.u16(0)
    Writer.i32(len(Stamps))
    for Entry in Stamps:
        Writer.i32(Entry.tree_id)
        Writer.u32(Entry.stamp.high)
        Writer.u32(Entry.stamp.low)
    Writer.raw(PackFields("<3iIi", *KManagerWords))
    Writer.begin_object(KListClass, 1)
    Writer.raw(PackFields(KCollectionFormat, *KCollectionWords))
    Writer.string("")
    Writer.raw(PackFields(KLastEditFormat, *KLastEditWords))


# the terminal reader binds both empty objects before checking that the stream has closed
def ReadCmgrTail(Cursor: ArchiveCursor, Generation: int) -> tuple[FeatureStamp, ...]:
    RequireArch(Generation, 19000, "modern CMgr tail generation")
    _ = Cursor.TakePointer((KListClass,), KDefinitionKind, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<H"), (0,), "first CMgr list count")
    (Count,) = Cursor.ReadInts("<i")
    RequireArch(0 <= Count <= 2, True, "CMgr feature stamp count")
    Entries = []
    for _ in range(Count):
        TreeId, High, Low = Cursor.ReadInts("<iII")
        Entries.append(FeatureStamp(TreeId, Stamp(High, Low)))
    Stamps = tuple(Entries)
    RequireStamps(Stamps)
    RequireArch(Cursor.ReadInts("<3iIi"), KManagerWords, "CMgr intermediate fields")
    _ = Cursor.TakePointer((KListClass,), KClassRefKind, CompactOnly=True)
    RequireArch(
        Cursor.ReadInts(KCollectionFormat), KCollectionWords, "CMgr collections"
    )
    RequireArch(Cursor.ReadText(), "", "CMgr last edit name")
    RequireArch(
        Cursor.ReadInts(KLastEditFormat), KLastEditWords, "CMgr last edit fields"
    )
    RequireArch(Cursor.Offset, len(Cursor.BlobValue), "CMgr tail end")
    return Stamps
