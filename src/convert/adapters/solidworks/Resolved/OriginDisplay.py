from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Container.Archive import KClassRefKind, ReadString
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor


# the origin still allocates display lists even when their contents are empty
@Dataclass(frozen=True, slots=True)
class OriginList:
    Offset: int
    ObjectIndex: int
    EndOffset: int


# the display map must retain its two empty list allocations in their saved order
def ReadOriginList(Cursor: ArchiveCursor) -> OriginList:
    Offset = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(
        ("suObList",), KClassRefKind, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<H"), (0,), "empty origin presentation list")
    return OriginList(Offset, ObjectIndex, Cursor.Offset)


# checked origin display and profile fields locate the following local plane reference
def ReadOrigViewMut(Cursor: ArchiveCursor) -> tuple[OriginList, OriginList]:
    RequireArch(Cursor.ReadInts("<7H"), (0,) * 7, "empty origin inline presentation")
    FirstList = ReadOriginList(Cursor)
    RequireArch(
        Cursor.ReadInts("<7H"), (0,) * 7, "guarded origin presentation counters"
    )
    RequireArch(Cursor.ReadInts("<HHi"), (2, 1, 2), "modern origin sketch state")
    RequireArch(
        Cursor.ReadInts("<15i"), (2,) + (1,) * 12 + (0, 1), "bent reference array"
    )
    RequireArch(Cursor.ReadInts("<4H"), (0,) * 4, "empty origin auxiliary groups")
    Label, Width = ReadString(Cursor.BlobValue, Cursor.Offset)
    RequireArch((Label, Width), ("", 4), "empty wide origin presentation label")
    Cursor.Offset += Width
    RequireArch(
        Cursor.ReadValue("<hf3i"), (-1, -1.0, -1, 1, -1), "default origin display"
    )
    RequireArch(Cursor.ReadPoint(3), (0, 0, 0), "origin display vector")
    RequireArch(Cursor.ReadInts("<I2i"), (1, 0, 0), "guarded origin display state")
    RequireArch(Cursor.ReadInts("<2H5i"), (0,) * 7, "empty origin display arrays")
    SecondList = ReadOriginList(Cursor)
    RequireArch(Cursor.ReadInts("<H7i"), (0,) * 8, "empty origin region trailer")
    RequireArch(Cursor.ReadInts("<Ii"), (0, 0), "empty origin profile chain")
    RequireArch(Cursor.ReadInts("<iB"), (3, 1), "absent origin kernel packet")
    RequireArch(
        Cursor.ReadInts("<iH2IH"), (0, 0, 0, 100000, 0), "empty origin profile maps"
    )
    return FirstList, SecondList
