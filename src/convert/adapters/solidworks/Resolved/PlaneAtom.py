from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor


# shared atom branches must agree on the fields following the partition pointer
def ReadAtomMaps(Cursor: ArchiveCursor) -> None:
    RequireArch(Cursor.ReadInts("<3i"), (0, 0, 0), "empty local partition fields")
    _ = Cursor.ReadInts("<i")
    RequireArch(Cursor.ReadInts("<3i"), (0, 0, 0), "empty atom maps")
    _ = Cursor.ReadInts("<i")
    RequireArch(
        Cursor.ReadInts("<4i"),
        (0, 0, 0, 0),
        "absent visual map animation and face labels",
    )
    _ = Cursor.ReadInts("<i")


# the principal and embedded planes share the local atom and rollback fields
def ReadPlaneAtom(Cursor: ArchiveCursor) -> tuple[int, int]:
    RequireArch(Cursor.ReadInts("<3H"), (0, 0, 0), "empty source atom lists and keeper")
    RequireArch(Cursor.ReadInts("<2i"), (0, 0), "absent transfer arrays")
    Cursor.ReadNull()
    CountValue, ModeValue = Cursor.ReadInts("<2i")
    RequireArch(CountValue, 0, "empty atom id list")
    RequireArch(ModeValue in range(4), True, "known atom body mode")
    ArrayOffset = Cursor.Offset
    RequireArch(Cursor.ReadInts("<i"), (0,), "absent profile atom array")
    _ = Cursor.ReadInts("<i")
    Chooser, FlagsValue, OtherChooser = Cursor.ReadInts("<3H")
    RequireArch((Chooser, OtherChooser), (0, 0), "absent base body choosers")
    _ = Cursor.ReadInts("<i")
    RequireArch(Cursor.ReadInts("<2H"), (0, 0), "absent additional body choosers")
    _ = Cursor.ReadInts("<i")
    RequireArch(Cursor.ReadInts("<i"), (0,), "absent action array")
    RequireArch(Cursor.ReadInts("<i"), (1,), "saved local partition record")
    Cursor.ReadNull()
    ReadAtomMaps(Cursor)
    return ArrayOffset, FlagsValue
