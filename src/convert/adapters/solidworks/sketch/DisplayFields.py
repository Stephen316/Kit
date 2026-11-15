from typing import cast as CastValue

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor


# compact null children are part of the same map as their containing display
def ReadNulls(Cursor: ArchiveCursor, Count: int) -> None:
    for _ in range(Count):
        Cursor.ReadNull()


# even an empty display title must consume its native string framing
def ReadEmptyTexts(Cursor: ArchiveCursor, Count: int) -> None:
    for _ in range(Count):
        RequireArch(Cursor.ReadText(), "", "empty depth display label")


# the two display types share numeric placement fields and framed labels
def ReadPlacement(Cursor: ArchiveCursor) -> None:
    ReadEmptyTexts(Cursor, 4)
    _ = Cursor.ReadPoint(22)
    _ = Cursor.ReadInts("<i7H")
    _ = Cursor.ReadPoint(3)


# the saved copies corroborate the authored dimension and the empty display additions
def ReadCache(Cursor: ArchiveCursor) -> tuple[float, float]:
    ReadNulls(Cursor, 2)
    PostFields = Cursor.ReadValue("<2d2i2HI2i")
    RequireArch(PostFields[-2:], (0, 0), "empty post dimension object arrays")
    ReadEmptyTexts(Cursor, 1)
    ReadNulls(Cursor, 2)
    State, Cached, *Settings, Placement = CastValue(
        tuple[int, float, int, int, int, int, float], Cursor.ReadValue("<id4Id")
    )
    RequireArch(
        (State, tuple(Settings)), (-1, (8, 16, 1, 1)), "guarded depth display cache"
    )
    ReadEmptyTexts(Cursor, 1)
    return Cached, Placement


# favorite settings may continue only along the guarded empty child routes
def ReadDisplayTail(Cursor: ArchiveCursor) -> None:
    Appearance = Cursor.ReadValue("<2iId2HI4didHi30Id")
    RequireArch(Appearance[:6], (0, -1, 0, -1, 1, 1), "guarded depth favorite style")
    ReadEmptyTexts(Cursor, 4)
    _ = Cursor.ReadInts("<2HiI")
    ReadNulls(Cursor, 3)
    RequireArch(Cursor.ReadInts("<I"), (1002101,), "guarded saved depth display flags")
    ReadNulls(Cursor, 2)
    RequireArch(
        Cursor.ReadInts("<3i"), (0, 0, 0), "empty additional depth display items"
    )
    Cursor.ReadNull()
    _ = Cursor.ReadValue("<5id6i")
    ReadEmptyTexts(Cursor, 2)
    _ = Cursor.ReadInts("<3i")
    ReadEmptyTexts(Cursor, 1)
    _ = Cursor.ReadValue("<2i3d2i")
    ReadEmptyTexts(Cursor, 1)
    _ = Cursor.ReadValue("<i5di")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<i"), (0,), "guarded distance display return")
