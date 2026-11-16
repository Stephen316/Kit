from datetime import datetime, timezone

from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

KInitialConfigTime = int(datetime(1990, 1, 1, tzinfo=timezone.utc).timestamp())


def RequireCmgrFront(Generation: int, BodyCount: int, SaveMode: int) -> None:
    RequireArch(
        type(Generation) is int and Generation == 19000,
        True,
        "CMgr collection opening generation",
    )
    RequireArch(
        type(BodyCount) is int and BodyCount in (0, 1),
        True,
        "CMgr collection opening standalone solid count",
    )
    RequireArch(
        type(SaveMode) is int and SaveMode == 1,
        True,
        "CMgr collection opening measured save mode",
    )


# This standalone profile has no alternate configurations or toolbox objects.
def WriteCmgrFront(
    Writer: ArchiveWriter, Generation: int, *, BodyCount: int, SaveMode: int
) -> None:
    RequireCmgrFront(Generation, BodyCount, SaveMode)
    Writer.u32(KInitialConfigTime)
    Writer.raw(EncodeNull())
    Writer.u16(0)
    Writer.i32(BodyCount)
    Writer.u8(0)
    Writer.u8(0)
    Writer.u16(0)
    Writer.u32(Generation)
    Writer.u8(SaveMode)
    Writer.u8(0)
    Writer.raw(EncodeNull())
    Writer.u16(0)


# A typed parse keeps null references distinct from the neighboring compact lists.
def ReadCmgrFront(
    Cursor: ArchiveCursor, Generation: int, *, BodyCount: int, SaveMode: int
) -> None:
    RequireCmgrFront(Generation, BodyCount, SaveMode)
    RequireArch(Cursor.ReadInts("<I"), (KInitialConfigTime,), "CMgr configuration time")
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<HiBBHIBB"),
        (0, BodyCount, 0, 0, 0, Generation, SaveMode, 0),
        "CMgr default configuration collections",
    )
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<H"), (0,), "CMgr fourth configuration list")
