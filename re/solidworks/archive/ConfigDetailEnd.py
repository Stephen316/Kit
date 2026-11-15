"""Finish the inline modern detail settings before the environment folder."""

from ConfigAnnoData import ReadAnnoHelper
from ConfigDetail import ReadCharFormat, ReadDetailNames


# center marks and both datum helpers each save the same annotation helper
def ReadDatumOptions(Cursor):
    Cursor.ReadValue("<BdBd6B")  # center mark
    ReadAnnoHelper(Cursor)
    Cursor.ReadValue("<I4Bd")

    Cursor.ReadValue("<3B2i")  # datum feature
    ReadDetailNames(Cursor, 2)
    Cursor.ReadValue("<3i")
    ReadAnnoHelper(Cursor)

    ReadDetailNames(Cursor, 5)  # datum target
    Cursor.ReadValue("<2i2di5Bidi3B")
    Cursor.ReadPoint(3)
    ReadAnnoHelper(Cursor)


# all following scalar option groups are enabled in generation 19000
def ReadSwiftOptions(Cursor):
    Cursor.ReadValue("<d2i")
    for _ in range(5):
        Cursor.ReadValue("<di")
    Cursor.ReadValue("<d2idid")
    for _ in range(4):
        Cursor.ReadValue("<3i2d")
    Cursor.ReadValue("<7i2d2i2d4i2d19i")

    Cursor.ReadValue("<5d2i")
    for _ in range(4):
        Cursor.ReadValue("<2d4i")
    Cursor.ReadValue("<15i")
    Cursor.ReadValue("<4d10i")
    Cursor.ReadValue("<4d12i")
    Cursor.ReadValue("<6i")


# the last options follow the eight print widths and contain variable-length templates
def ReadDetailEnd(Cursor):
    ReadDatumOptions(Cursor)
    ReadSwiftOptions(Cursor)
    Cursor.ReadValue("<8f")
    Cursor.ReadValue("<d2i2B6i6d9i")
    ReadCharFormat(Cursor)
    ReadCharFormat(Cursor)
    Cursor.ReadValue("<4i")
    ReadDetailNames(Cursor, 4)
    Cursor.ReadValue("<4i")
    Cursor.ReadText()
    Cursor.ReadValue("<4i")
    ReadDetailNames(Cursor, 3)
    Cursor.ReadValue("<5i")
