from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from typing import TypeAlias

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

# saved region rows retain native identifiers independently of their display values
KRegionRow: TypeAlias = tuple[int, int, float]


# region properties must consume their framed labels before the next group can begin
def ReadRegionProps(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadPoint(12)
    _ = Cursor.ReadValue("<5i")
    _ = Cursor.ReadPoint(1)
    _ = Cursor.ReadValue("<4i")
    _ = Cursor.ReadText()
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<i")
    _ = Cursor.ReadPoint(3)
    for _ in range(3):
        _ = Cursor.ReadPoint(3)
    _ = Cursor.ReadValue("<iH")


# each populated inline group owns its property payload before the next group begins
def ReadRegions(Cursor: ArchiveCursor) -> list[list[KRegionRow]]:
    RequireArch(Cursor.ReadCount(), 0, "empty modern model text-pair table")
    _ = Cursor.ReadValue("<iB2i")
    Count = Cursor.ReadCount()
    RequireArch(Count in (0, 1, 2), True, "witnessed model region groups")
    Regions: list[list[KRegionRow]] = []
    for _ in range(Count):
        ItemCount = Cursor.ReadCount()
        RequireArch(ItemCount in (0, 1), True, "witnessed model region group size")
        Items: list[KRegionRow] = []
        for _ in range(ItemCount):
            BodyId, RegionId = Cursor.ReadInts("<2i")
            (Scalar,) = Cursor.ReadPoint(1)
            Items.append((BodyId, RegionId, Scalar))
        if Items:
            ReadRegionProps(Cursor)
        Regions.append(Items)
    if Count == 2:
        _ = Cursor.ReadValue("<i")
    _ = Cursor.ReadValue("<i")
    return Regions


# the ordinary part ends with three empty optional routes and four scalar fields
def ReadPartReturn(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<2i")
    RequireArch(Cursor.ReadValue("<i"), (0,), "absent supplemental link data")
    RequireArch(Cursor.ReadCount(), 0, "empty sheet metal extension array")
    RequireArch(Cursor.ReadCount(), 0, "empty part object table")
    *_, SolverMode = Cursor.ReadValue("<iI2i")
    RequireArch(SolverMode, 0, "absent part solver table")
