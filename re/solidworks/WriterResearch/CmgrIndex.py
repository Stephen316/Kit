from dataclasses import dataclass as Dataclass

from CmgrBaseHeader import KStandaloneFlags
from CmgrOpening import KFirstConfigurationId
from convert.adapters.solidworks.Container.Archive import KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import KDefaultConfigName
from convert.adapters.solidworks.Container.Definition import (
    ArchiveWriter,
    KFirstLoadArrayIndex,
)

KConfigurationIndex = "Contents/CMgrHdr2"
KManagerHeaderClass = "dmConfigMgrHeader_c"
KConfigurationHeaderClass = "dmConfigHeader_c"
KDefaultTreeSortOrder = 2
KDefaultTransformStamp = 101


@Dataclass(frozen=True, slots=True)
class CmgrIndex:
    ConfigId: int
    NameValue: str
    SessionStamp: int
    GeometryStamp: int
    LastSavedTime: int


# The supported index has one active, rebuilt ordinary part configuration.
def RequireCmgrIndex(Generation: int, Fields: CmgrIndex) -> None:
    RequireArch(
        (
            type(Generation),
            Generation,
            type(Fields.ConfigId),
            Fields.ConfigId,
            Fields.NameValue,
        ),
        (int, 19000, int, KFirstConfigurationId, KDefaultConfigName),
        "standalone CMgr configuration index scope",
    )
    RequireArch(
        all(
            type(Value) is int and 0 < Value <= 0xFFFFFFFF
            for Value in (Fields.SessionStamp, Fields.GeometryStamp)
        ),
        True,
        "CMgr index document counters",
    )
    RequireArch(
        type(Fields.LastSavedTime) is int and 0 < Fields.LastSavedTime <= 0x7FFFFFFF,
        True,
        "CMgr index save time",
    )


def EncodeCmgrIndex(Generation: int, Fields: CmgrIndex) -> bytes:
    RequireCmgrIndex(Generation, Fields)
    Writer = ArchiveWriter()
    Writer.begin_object(KManagerHeaderClass, 1)
    Writer.u16(1)
    Writer.begin_object(KConfigurationHeaderClass, 1)
    Writer.i32(1)
    Writer.string(Fields.NameValue)
    Writer.i32(Fields.ConfigId)
    Writer.u32(Fields.SessionStamp)
    Writer.string(Fields.NameValue)
    Writer.i32(-1)
    Writer.i32(0)
    Writer.string("")
    Writer.string("")
    Writer.u32(KStandaloneFlags)
    Writer.i32(0)
    Writer.u32(Fields.GeometryStamp)
    Writer.u32(KDefaultTransformStamp)
    Writer.u32(Fields.LastSavedTime)
    Writer.i32(KDefaultTreeSortOrder)
    return Writer.build()


def ReadCmgrIndex(BlobValue: bytes, Generation: int) -> CmgrIndex:
    Cursor = ArchiveCursor(BlobValue, 0, KFirstLoadArrayIndex, {}, {})
    _ = Cursor.TakePointer((KManagerHeaderClass,), KDefinitionKind, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<H"), (1,), "one CMgr index configuration")
    _ = Cursor.TakePointer(
        (KConfigurationHeaderClass,), KDefinitionKind, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<i"), (1,), "active CMgr index configuration")
    NameValue = Cursor.ReadText()
    ConfigId, SessionStamp = Cursor.ReadInts("<iI")
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadInts("<ii")),
        (NameValue, (-1, 0)),
        "CMgr index display name, absent parent and clean rebuild state",
    )
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadText(), Cursor.ReadInts("<Ii")),
        ("", "", (KStandaloneFlags, 0)),
        "CMgr index comment, alternate name and standalone options",
    )
    GeometryStamp, TransformStamp, LastSavedTime, TreeSortOrder = Cursor.ReadInts(
        "<IIIi"
    )
    RequireArch(
        (TransformStamp, TreeSortOrder, Cursor.Offset),
        (KDefaultTransformStamp, KDefaultTreeSortOrder, len(BlobValue)),
        "CMgr index native transform stamp and return",
    )
    Fields = CmgrIndex(ConfigId, NameValue, SessionStamp, GeometryStamp, LastSavedTime)
    RequireCmgrIndex(Generation, Fields)
    return Fields
