"""Read modern geometric tolerance settings and their two optional frame arms."""

from ConfigAnnoData import ReadAnnoHelper
from ConfigDetail import ReadCharFormat, ReadDetailNames, ReadShortNames
from SketchRoot import Require


# each counted frame ends with two typed tolerance pointers before any indicators
def ReadTolFrame(Cursor, ReadNull):
    Cursor.ReadText()
    for _ in range(2):
        Cursor.ReadValue("<B")
        ReadDetailNames(Cursor, 2)
    for _ in range(6):
        ReadShortNames(Cursor)
    Cursor.ReadValue("<2i")
    Require(Cursor.ReadValue("<H"), (0,), "tolerance frame without datum records")
    ReadNull()
    ReadNull()
    Require(Cursor.ReadCount(), 0, "empty tolerance indicator list")


# the helper is inline but delegates its nullable tolerance children to the map reader
def ReadTolData(Cursor, ReadNull):
    for _ in range(Cursor.ReadCount()):
        ReadTolFrame(Cursor, ReadNull)
    Cursor.ReadValue("<2i")
    Cursor.ReadText()
    Cursor.ReadValue("<4BiB")
    for _ in range(2):
        ReadDetailNames(Cursor, 2)
        Cursor.ReadValue("<B")
    Cursor.ReadText()
    Cursor.ReadValue("<4B")
    ReadCharFormat(Cursor)
    ReadAnnoHelper(Cursor)
    Cursor.ReadValue("<6B")
