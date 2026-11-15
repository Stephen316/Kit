from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.config.AnnotationData import ReadAnnoHelper
from convert.adapters.solidworks.config.Detail import ReadCharFormat, ReadDetailNames


# center marks and both datum helpers each save the same annotation helper
def ReadDatumOpts(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<BdBd6B")
    ReadAnnoHelper(Cursor)
    _ = Cursor.ReadValue("<I4Bd")

    _ = Cursor.ReadValue("<3B2i")
    ReadDetailNames(Cursor, 2)
    _ = Cursor.ReadValue("<3i")
    ReadAnnoHelper(Cursor)

    ReadDetailNames(Cursor, 5)
    _ = Cursor.ReadValue("<2i2di5Bidi3B")
    _ = Cursor.ReadPoint(3)
    ReadAnnoHelper(Cursor)


# all following scalar option groups are enabled in generation 19000
def ReadSwiftOpts(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<d2i")
    for _ in range(5):
        _ = Cursor.ReadValue("<di")
    _ = Cursor.ReadValue("<d2idid")
    for _ in range(4):
        _ = Cursor.ReadValue("<3i2d")
    _ = Cursor.ReadValue("<7i2d2i2d4i2d19i")

    _ = Cursor.ReadValue("<5d2i")
    for _ in range(4):
        _ = Cursor.ReadValue("<2d4i")
    _ = Cursor.ReadValue("<15i")
    _ = Cursor.ReadValue("<4d10i")
    _ = Cursor.ReadValue("<4d12i")
    _ = Cursor.ReadValue("<6i")


# the last options follow the eight print widths and contain variablelength templates
def ReadDetailEnd(Cursor: ArchiveCursor) -> None:
    ReadDatumOpts(Cursor)
    ReadSwiftOpts(Cursor)
    _ = Cursor.ReadValue("<8f")
    _ = Cursor.ReadValue("<d2i2B6i6d9i")
    ReadCharFormat(Cursor)
    ReadCharFormat(Cursor)
    _ = Cursor.ReadValue("<4i")
    ReadDetailNames(Cursor, 4)
    _ = Cursor.ReadValue("<4i")
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<4i")
    ReadDetailNames(Cursor, 3)
    _ = Cursor.ReadValue("<5i")
