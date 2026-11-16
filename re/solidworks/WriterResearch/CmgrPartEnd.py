from struct import pack as PackFields

from convert.adapters.solidworks.Container.Archive import (
    KBigObjectTag,
    KObjectRefKind,
    EncodeNull,
    EncodeObjectRef,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import KConfigClass
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

KListCountsAndFlags = (0,) * 12
KLastListFields = (0, 0, 0, 0)
KPartEndFields = (0, 0, -1, -1, 0, 0)


# the native standalone path leaves out the condition one fields
def RequirePartScope(Generation: int, ConditionOne: bool) -> None:
    RequireArch((Generation, ConditionOne), (19000, False), "CMgr part suffix scope")


# map enumeration order belongs to each save and ids must remain unique
def RequireAtomIds(AtomIds: tuple[int, ...]) -> None:
    RequireArch(
        len(AtomIds) == len(set(AtomIds)) <= 2
        and all(0 < AtomId <= 0x7FFFFFFF for AtomId in AtomIds),
        True,
        "CMgr part atom identifiers",
    )


# the constructor can emit the unfrozen part return from explicit atom identities
def WriteCmgrPartEnd(
    Writer: ArchiveWriter,
    *,
    Generation: int,
    ConditionOne: bool,
    AtomIds: tuple[int, ...],
) -> None:
    RequirePartScope(Generation, ConditionOne)
    RequireAtomIds(AtomIds)
    Writer.raw(PackFields("<2i", 1, -1))
    Writer.raw(EncodeNull() * 2)
    Writer.raw(PackFields("<12H", *KListCountsAndFlags))
    Writer.raw(PackFields("<H2iH", *KLastListFields))
    Writer.raw(EncodeNull() * 3)
    Writer.f64(-1.0)
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<2i", 0, 0))
    Writer.raw(EncodeNull() * 2)
    Writer.raw(PackFields("<I2i", 0, -1, len(AtomIds)))
    for AtomId in AtomIds:
        Writer.raw(PackFields("<2i", AtomId, 0))
    Writer.raw(PackFields("<4i2I", *KPartEndFields))


# each optional part pointer must be absent to retain the enclosing map
def ReadCmgrPartEnd(
    Cursor: ArchiveCursor, *, Generation: int, ConditionOne: bool
) -> tuple[int, ...]:
    RequirePartScope(Generation, ConditionOne)
    RequireArch(Cursor.ReadInts("<2i"), (1, -1), "CMgr inline part object")
    Cursor.ReadNull()
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<12H"), KListCountsAndFlags, "CMgr part list fields")
    RequireArch(Cursor.ReadInts("<H2iH"), KLastListFields, "CMgr part final list")
    for _ in range(3):
        Cursor.ReadNull()
    RequireArch(Cursor.ReadPoint(1), (-1.0,), "CMgr unassigned hatch scale")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<2i"), (0, 0), "CMgr empty body appearances")
    Cursor.ReadNull()
    Cursor.ReadNull()
    Checksum, Sentinel, Count = Cursor.ReadInts("<I2i")
    RequireArch((Checksum, Sentinel), (0, -1), "CMgr unfrozen part fields")
    RequireArch(0 <= Count <= 2, True, "CMgr part atom count")
    Entries = []
    for _ in range(Count):
        AtomId, Value = Cursor.ReadInts("<2i")
        RequireArch(Value, 0, "CMgr default part atom value")
        Entries.append(AtomId)
    AtomIds = tuple(Entries)
    RequireAtomIds(AtomIds)
    RequireArch(Cursor.ReadInts("<4i2I"), KPartEndFields, "CMgr part return fields")
    return AtomIds


# manager aliases must point back to the same part already in the archive map
def ReadCmgrAliases(Cursor: ArchiveCursor, PartIndex: int) -> None:
    _, _, Active = Cursor.TakePointer((KConfigClass,), KObjectRefKind, CompactOnly=True)
    RequireArch(
        Cursor.ReadInts("<iH"), (1, 1), "CMgr next configuration ID and list count"
    )
    _, _, Listed = Cursor.TakePointer((KConfigClass,), KObjectRefKind, CompactOnly=True)
    RequireArch((Active, Listed), (PartIndex, PartIndex), "CMgr part aliases")
    RequireArch(Cursor.ReadInts("<i"), (1,), "CMgr external object count")


# The one listed configuration must reuse the part allocation and its assigned ID.
def WriteCmgrAliases(
    Writer: ArchiveWriter,
    *,
    Generation: int,
    PartIndex: int,
    PartId: int,
    ExternalCount: int,
) -> None:
    RequireArch(
        (
            type(Generation),
            Generation,
            type(PartId),
            PartId,
            type(ExternalCount),
            ExternalCount,
        ),
        (int, 19000, int, 0, int, 1),
        "CMgr first standalone configuration with one external object",
    )
    ClassIndex = Writer.classes.get(KConfigClass)
    RequireArch(
        type(ClassIndex) is int
        and type(PartIndex) is int
        and 0 < ClassIndex < PartIndex < min(Writer.next_index, KBigObjectTag)
        and PartIndex == ClassIndex + 1,
        True,
        "CMgr published part allocation",
    )
    Reference = EncodeObjectRef(PartIndex)
    Writer.raw(Reference)
    Writer.i32(PartId + 1)
    Writer.u16(1)
    Writer.raw(Reference)
    Writer.i32(ExternalCount)
