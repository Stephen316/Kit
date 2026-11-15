"""Read the inline drawing label settings before the annotation helpers."""

from ConfigDetail import ReadCharFormat, ReadLineWidth
from SketchRoot import Require


# the shared drawing label contains two names, two line widths and six fonts
def ReadLabelStyle(Cursor, Format):
    Cursor.ReadValue("<11i")
    Require(Cursor.ReadValue("<h"), (-1,), "label settings without a layer")
    Cursor.ReadText()
    Cursor.ReadText()
    Cursor.ReadValue("<I2i")
    for _ in range(2):
        ReadCharFormat(Cursor)
    for _ in range(2):
        ReadLineWidth(Cursor)
    for _ in range(4):
        ReadCharFormat(Cursor)
    Cursor.ReadValue(Format)


# both the orthographic and miscellaneous members use the orthographic serializer
def ReadLabelDefs(Cursor):
    Cursor.ReadValue("<2i")
    ReadLabelStyle(Cursor, "<Ii")  # detail
    ReadLabelStyle(Cursor, "<3d5i")  # section
    ReadLabelStyle(Cursor, "<i")  # auxiliary
    ReadCharFormat(Cursor)
    ReadLabelStyle(Cursor, "<2i")  # orthographic
    ReadLabelStyle(Cursor, "<2i")  # miscellaneous
