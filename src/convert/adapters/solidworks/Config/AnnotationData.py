from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Config.Detail import ReadCharFormat, ReadDetailNames
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# these helper records share an inline font and two leader settings groups
def ReadAnnoHelper(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<4iB")
    ReadCharFormat(Cursor)
    for _ in range(2):
        _ = Cursor.ReadValue("<Bidi")


# the current surface finish helper stores both legacy and supplemental text
def ReadFinishData(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<i")
    ReadDetailNames(Cursor, 10)
    _ = Cursor.ReadValue("<4Bi4BdB")
    ReadCharFormat(Cursor)
    _ = Cursor.ReadValue("<2B")
    ReadAnnoHelper(Cursor)
    _ = Cursor.ReadValue("<id")
    ReadDetailNames(Cursor, 2)
    _ = Cursor.ReadValue("<2i")


# the note map is counted separately from the inline annotation helper
def ReadNoteData(Cursor: ArchiveCursor) -> None:
    ReadDetailNames(Cursor, 4)
    _ = Cursor.ReadValue("<6BidB")
    _ = Cursor.ReadValue("<8i2d12B")
    ReadCharFormat(Cursor)
    _ = Cursor.ReadValue("<2i")
    RequireArch(Cursor.ReadValue("<Q"), (0,), "empty note helper map")
    _ = Cursor.ReadValue("<3B")
    ReadAnnoHelper(Cursor)
    _ = Cursor.ReadValue("<2Bid2i")
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<4i2di2B")


# weld settings inline two additional fonts and two surface finish helpers
def ReadWeldData(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<B")
    ReadDetailNames(Cursor, 17)
    _ = Cursor.ReadValue("<4B")
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<2B2i3B2i3Bi2B")
    ReadDetailNames(Cursor, 5)
    _ = Cursor.ReadValue("<7B")
    ReadCharFormat(Cursor)
    for _ in range(2):
        _ = Cursor.ReadValue("<B")
        ReadCharFormat(Cursor)
    for _ in range(2):
        ReadFinishData(Cursor)
