from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Config.Detail import ReadCharFormat, ReadLineWidth
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# each table inherits the two line widths and character format of its general base
def ReadTableBase(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<2iI")
    RequireArch(Cursor.ReadValue("<h"), (-1,), "table settings without a layer")
    _ = Cursor.ReadValue("<i")
    for _ in range(2):
        ReadLineWidth(Cursor)
    ReadCharFormat(Cursor)


# the modern member order places the common font after the hole table
def ReadTableDefs(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<i")
    ReadTableBase(Cursor)
    ReadTableBase(Cursor)
    _ = Cursor.ReadValue("<3iIi")
    _ = Cursor.ReadText()

    ReadTableBase(Cursor)
    _ = Cursor.ReadValue("<I")
    for _ in range(3):
        _ = Cursor.ReadText()

    ReadTableBase(Cursor)
    _ = Cursor.ReadValue("<2i2d10i")
    ReadCharFormat(Cursor)
    ReadTableBase(Cursor)
    for Format in ("<i", "<4i", "<2i2d6i", "<I"):
        ReadTableBase(Cursor)
        _ = Cursor.ReadValue(Format)
    _ = Cursor.ReadPoint(2)
