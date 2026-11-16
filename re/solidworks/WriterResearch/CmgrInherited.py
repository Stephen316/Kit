from struct import pack as PackFields

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import Stamp
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# these feature version values describe the pinned generation and application build
KBuildVersion = 2026225
KFileSession = 370108
KFeatureDisplay = (0, 65535, 0, 3, 0xFFFFFFFF, 65535, -1, -1.0)
KFeatureReturn = (0, 4, 0, 0, 0, -1)
KFeatureEnd = (2, KFileSession, 1)


# manager and part features take independent high and low words from their callers
def RequireCmgrTime(Generation: int, StampValue: Stamp) -> None:
    RequireArch(Generation, 19000, "CMgr inherited feature generation")
    RequireArch(
        all(
            type(Word) is int and 0 <= Word <= 0xFFFFFFFF
            for Word in (StampValue.high, StampValue.low)
        ),
        True,
        "CMgr unsigned FILETIME words",
    )


# both native classes inherit the same default feature fields and stamp encoding
def WriteCmgrFeature(Writer: ArchiveWriter, Generation: int, StampValue: Stamp) -> None:
    RequireCmgrTime(Generation, StampValue)
    Writer.raw(
        PackFields("<iiIBiiiidi", 0, 0, 101, 0, 0, 0, 0, Generation, 0.0, KBuildVersion)
    )
    Writer.u16(0)
    Writer.string("")
    Writer.raw(PackFields("<BHHBIHhf", *KFeatureDisplay))
    Writer.i32(0)
    Writer.i32(0)
    Writer.u16(0)
    Writer.raw(
        PackFields(
            "<IBBiiiIIHii",
            *KFeatureReturn,
            StampValue.high,
            StampValue.low,
            *KFeatureEnd,
        )
    )


# timestamps vary independently of the constructor fields in the two features
def ReadCmgrFeature(Cursor: ArchiveCursor, Generation: int) -> Stamp:
    RequireArch(Generation, 19000, "CMgr inherited feature generation")
    RequireArch(
        Cursor.ReadInts("<iiIBiiiiQi"),
        (0, 0, 101, 0, 0, 0, 0, Generation, 0, KBuildVersion),
        "CMgr inherited feature opening",
    )
    Cursor.ReadNull()
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadValue("<BHHBIHhf")),
        ("", KFeatureDisplay),
        "CMgr inherited feature display style",
    )
    RequireArch(Cursor.ReadInts("<2i"), (0, 0), "CMgr inherited feature members")
    Cursor.ReadNull()
    Fields = Cursor.ReadInts("<IBBiiiIIHii")
    RequireArch(
        (Fields[:6], Fields[8:]),
        (KFeatureReturn, KFeatureEnd),
        "CMgr inherited feature return",
    )
    return Stamp(Fields[6], Fields[7])
