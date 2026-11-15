"""Read the inline presentation helper fields before the tolerance frames."""

from ConfigDetail import ReadCharFormat, ReadDetailNames
from SketchRoot import Require


# these helper records share an inline font and two leader settings groups
def ReadAnnoHelper(Cursor):
    Cursor.ReadValue("<4iB")
    ReadCharFormat(Cursor)
    for _ in range(2):
        Cursor.ReadValue("<Bidi")


# the current surface finish helper stores both legacy and supplemental text
def ReadFinishData(Cursor):
    Cursor.ReadValue("<i")
    ReadDetailNames(Cursor, 10)
    Cursor.ReadValue("<4Bi4BdB")
    ReadCharFormat(Cursor)
    Cursor.ReadValue("<2B")
    ReadAnnoHelper(Cursor)
    Cursor.ReadValue("<id")
    ReadDetailNames(Cursor, 2)
    Cursor.ReadValue("<2i")


# the note map is counted separately from the inline annotation helper
def ReadNoteData(Cursor):
    ReadDetailNames(Cursor, 4)
    Cursor.ReadValue("<6BidB")
    Cursor.ReadValue("<8i2d12B")
    ReadCharFormat(Cursor)
    Cursor.ReadValue("<2i")
    Require(Cursor.ReadValue("<Q"), (0,), "empty note helper map")
    Cursor.ReadValue("<3B")
    ReadAnnoHelper(Cursor)
    Cursor.ReadValue("<2Bid2i")
    Cursor.ReadText()
    Cursor.ReadValue("<4i2di2B")


# weld settings inline two additional fonts and two surface finish helpers
def ReadWeldData(Cursor):
    Cursor.ReadValue("<B")
    ReadDetailNames(Cursor, 17)
    Cursor.ReadValue("<4B")
    Cursor.ReadText()
    Cursor.ReadValue("<2B2i3B2i3Bi2B")
    ReadDetailNames(Cursor, 5)
    Cursor.ReadValue("<7B")
    ReadCharFormat(Cursor)
    for _ in range(2):
        Cursor.ReadValue("<B")
        ReadCharFormat(Cursor)
    for _ in range(2):
        ReadFinishData(Cursor)
