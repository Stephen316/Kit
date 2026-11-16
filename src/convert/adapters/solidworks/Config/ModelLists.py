from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Config.PointerReader import PointerReader
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
)


# absent child records have an archive count even when the array is inline
def ReadDisplayData(Cursor: ArchiveCursor, ReadPointer: PointerReader) -> None:
    _ = Cursor.ReadValue("<2i")
    for _ in range(Cursor.ReadCount()):
        _ = Cursor.ReadValue("<i")
    _ = ReadPointer(KNullKind)
    _ = Cursor.ReadValue("<I")
    for _ in range(Cursor.ReadCount()):
        _ = Cursor.ReadValue("<i")
    for _ in range(8):
        RequireArch(Cursor.ReadValue("<H"), (0,), "empty inline model array")
    _ = ReadPointer(KNullKind)
    RequireArch(Cursor.ReadValue("<H"), (0,), "empty inline model object list")


# populated maps solver state and print settings select bodies outside this layout
def ReadMarkerTail(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<i")
    _ = Cursor.ReadValue("<i")
    RequireArch(Cursor.ReadCount(), 0, "empty model atom map")
    RequireArch(Cursor.ReadValue("<i"), (0,), "absent model solver data")
    RequireArch(Cursor.ReadCount(), 0, "empty model dimension map")
    _ = Cursor.ReadValue("<i")
    RequireArch(Cursor.ReadCount(), 0, "empty first dimension increment array")
    _ = Cursor.ReadValue("<i")
    RequireArch(Cursor.ReadCount(), 0, "empty second dimension increment array")
    _ = Cursor.ReadValue("<2i")
    RequireArch(Cursor.ReadValue("<i"), (0,), "absent 3D print settings")


# the list body and following two model names precede the typed thread manager
def ReadModelLists(Cursor: ArchiveCursor, ReadPointer: PointerReader) -> None:
    ReadDisplayData(Cursor, ReadPointer)
    _ = ReadPointer(KDefinitionKind, "moPMarkRecord_c")
    ReadMarkerTail(Cursor)
    _ = ReadPointer(KClassRefKind, "suObList")
    RequireArch(Cursor.ReadValue("<H"), (0,), "empty saved model list")
    _ = Cursor.ReadValue("<i")
    _ = Cursor.ReadText()
    _ = Cursor.ReadText()
    _ = ReadPointer(KDefinitionKind, "moCThreadRefMgr_c")
    RequireArch(Cursor.ReadCount(), 0, "empty cosmetic thread reference list")
    _ = Cursor.ReadValue("<i")
    _ = ReadPointer(KNullKind)
