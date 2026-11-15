"""Read the inline modern table settings between annotation and label settings."""

from ConfigDetail import ReadCharFormat, ReadLineWidth
from SketchRoot import Require


# each table inherits the two line widths and character format of its general base
def ReadTableBase(Cursor):
    Cursor.ReadValue("<2iI")
    Require(Cursor.ReadValue("<h"), (-1,), "table settings without a layer")
    Cursor.ReadValue("<i")
    for _ in range(2):
        ReadLineWidth(Cursor)
    ReadCharFormat(Cursor)


# the modern member order places the common font after the hole table
def ReadTableDefs(Cursor):
    Cursor.ReadValue("<i")
    ReadTableBase(Cursor)  # general
    ReadTableBase(Cursor)  # revision
    Cursor.ReadValue("<3iIi")
    Cursor.ReadText()

    ReadTableBase(Cursor)  # bill of materials
    Cursor.ReadValue("<I")
    for _ in range(3):
        Cursor.ReadText()

    ReadTableBase(Cursor)  # hole
    Cursor.ReadValue("<2i2d10i")
    ReadCharFormat(Cursor)
    ReadTableBase(Cursor)  # title block
    for Format in ("<i", "<4i", "<2i2d6i", "<I"):  # weld, bend, punch, family
        ReadTableBase(Cursor)
        Cursor.ReadValue(Format)
    Cursor.ReadPoint(2)
