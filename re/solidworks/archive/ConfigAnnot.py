"""Read the inline annotation settings before the modern table settings."""

from ConfigDetail import ReadCharFormat, ReadLineWidth
from SketchRoot import Require

# the middle annotation members add only their own scalar fields to the shared base
KAnnotTails = (
    "<3i3di",  # note
    "<6i",  # datum
    "<2iH",  # geometric tolerance, including its wide character
    "<2i2d",  # surface finish
)


# the supported base retains an inline font and leaves the layer pointer absent
def ReadAnnotBase(Cursor):
    Cursor.ReadValue("<id6i")
    Require(Cursor.ReadValue("<h"), (-1,), "annotation settings without a layer")
    for _ in range(2):
        ReadLineWidth(Cursor)
    ReadCharFormat(Cursor)
    Cursor.ReadValue("<i")


# balloon settings interleave property and text names with their scalar options
def ReadBalloonTail(Cursor):
    Cursor.ReadValue("<6i")
    Cursor.ReadText()
    Cursor.ReadText()
    Cursor.ReadValue("<I2d2i")
    Cursor.ReadText()
    Cursor.ReadValue("<3di")


# the document saves these inline members in the order used by the modern serializer
def ReadAnnotDefs(Cursor):
    Cursor.ReadValue("<id5iI4i")
    ReadAnnotBase(Cursor)
    ReadBalloonTail(Cursor)
    for Format in KAnnotTails:
        ReadAnnotBase(Cursor)
        Cursor.ReadValue(Format)

    # Weld records store a secondary character format.
    ReadAnnotBase(Cursor)
    Cursor.ReadValue("<i")
    ReadCharFormat(Cursor)

    # Bend notes precede the plain base and the two remaining view annotations.
    ReadAnnotBase(Cursor)
    Cursor.ReadValue("<3id")
    ReadAnnotBase(Cursor)
    ReadAnnotBase(Cursor)
    Cursor.ReadPoint(1)  # revision cloud
    ReadAnnotBase(Cursor)
    Cursor.ReadValue("<4ididi")  # view location label
