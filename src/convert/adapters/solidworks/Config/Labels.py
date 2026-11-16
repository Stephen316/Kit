from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Config.Detail import ReadCharFormat, ReadLineWidth
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# the shared drawing label contains two names two line widths and six fonts
def ReadLabelStyle(Cursor: ArchiveCursor, Format: str) -> None:
    _ = Cursor.ReadValue("<11i")
    RequireArch(Cursor.ReadValue("<h"), (-1,), "label settings without a layer")
    _ = Cursor.ReadText()
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<I2i")
    for _ in range(2):
        ReadCharFormat(Cursor)
    for _ in range(2):
        ReadLineWidth(Cursor)
    for _ in range(4):
        ReadCharFormat(Cursor)
    _ = Cursor.ReadValue(Format)


# both the orthographic and miscellaneous members use the orthographic serializer
def ReadLabelDefs(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<2i")
    ReadLabelStyle(Cursor, "<Ii")
    ReadLabelStyle(Cursor, "<3d5i")
    ReadLabelStyle(Cursor, "<i")
    ReadCharFormat(Cursor)
    ReadLabelStyle(Cursor, "<2i")
    ReadLabelStyle(Cursor, "<2i")
