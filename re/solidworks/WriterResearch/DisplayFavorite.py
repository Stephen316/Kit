from struct import pack as PackFields

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import (
    KBigObjectTag,
    KClassRefKind,
    KMaxMapIndex,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# the favorite occurrence uses the earlier class definition in the resolved archive
KFavoriteClass = "moFavoriteHandle_c"
KFavoriteSchema = 1

# the general display constructor allocates an unselected ordinary favorite
KFavoriteType = 0
KAbsentFavorite = -1
KInitialAuxiliary = 0


# the scoped close uses the ordinary modern part route with absent favorite settings
def RequireClose(Generation: int, DisplayMode: int, ConditionOne: bool) -> None:
    RequireArch(
        (Generation, DisplayMode, ConditionOne),
        (KConfigGen, 201, False),
        "witnessed ordinary distance display close",
    )


# a previously allocated class yields one new object in the enclosing map
def WriteFavorMut(
    Writer: ArchiveWriter, *, Generation: int, DisplayMode: int, ConditionOne: bool
) -> int:
    RequireClose(Generation, DisplayMode, ConditionOne)
    ClassIndex = Writer.classes.get(KFavoriteClass, 0)
    ObjectIndex = Writer.next_index
    RequireArch(
        0 < ClassIndex < KBigObjectTag and ClassIndex < ObjectIndex < KMaxMapIndex,
        True,
        "existing compact favorite class and available object slot",
    )
    Writer.begin_object(KFavoriteClass, KFavoriteSchema)
    Writer.raw(PackFields("<2iI", KFavoriteType, KAbsentFavorite, KInitialAuxiliary))
    return ObjectIndex


# the favorite serializer ends at its third field before outer display properties resume
def ReadFavorMut(
    Cursor: ArchiveCursor, *, Generation: int, DisplayMode: int, ConditionOne: bool
) -> int:
    RequireClose(Generation, DisplayMode, ConditionOne)
    TagValue = ReadTag(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        (TagValue.kind, TagValue.wide), (KClassRefKind, False), "compact favorite class"
    )
    Fields = FieldCursor(Cursor.BlobValue, Cursor.Offset + TagValue.size)
    RequireArch(
        Fields.ReadInts("<2iI"),
        (KFavoriteType, KAbsentFavorite, KInitialAuxiliary),
        "unselected ordinary display favorite",
    )
    _, _, ObjectIndex = Cursor.TakePointer(
        (KFavoriteClass,), KClassRefKind, CompactOnly=True
    )
    Cursor.Offset = Fields.Offset
    return ObjectIndex
