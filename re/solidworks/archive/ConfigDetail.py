"""Read the witnessed modern document detail settings through the first length pointer."""

from SketchRoot import Require


# each archived string must consume at least its length prefix
def ReadDetailNames(Cursor, Count):
    Require(
        0 <= Count <= len(Cursor.BlobValue) - Cursor.Offset,
        True,
        "bounded detail name count",
    )
    for _ in range(Count):
        Cursor.ReadText()


# modern detail definitions store exclusions before two groups of fixed scalar rows
def ReadDetailHead(Cursor):
    Cursor.ReadValue("<i")
    Cursor.ReadText()
    Cursor.ReadValue("<dBIid5Bi")
    for _ in range(2):
        Cursor.ReadValue("<3I3d")
    Cursor.ReadValue("<i2d9i")
    Cursor.ReadValue("<B4i2B2h2idi")
    for _ in range(2):
        Cursor.ReadText()
        Cursor.ReadValue("<i")
    Cursor.ReadValue("<12i")
    (ExclusionCount,) = Cursor.ReadValue("<i")
    ReadDetailNames(Cursor, ExclusionCount)
    Cursor.ReadValue("<3i")
    for _ in range(6):
        Cursor.ReadValue("<8i")
    (LabelCount,) = Cursor.ReadValue("<H")
    Require(LabelCount != 0xFFFF, True, "short priority label count")
    ReadDetailNames(Cursor, LabelCount)


# inline character formatting starts with the framed font name
def ReadCharFormat(Cursor):
    Cursor.ReadText()
    Cursor.ReadValue("<didI5dI")


# the first indexed dimension style shares its base with the other variants
def ReadStyleHead(Cursor):
    Cursor.ReadValue("<3i2di2d2i")
    Cursor.ReadText()
    Cursor.ReadText()
    Cursor.ReadValue("<2d8i")
    Require(Cursor.ReadValue("<h"), (-1,), "dimension style without a layer")
    Cursor.ReadValue("<2iI")


# the subtype carries a length code after the common scalar unit settings
def ReadLengthCode(Cursor):
    Cursor.ReadValue("<2i")
    Cursor.ReadPoint(1)
    Cursor.ReadValue("<2i")
    Cursor.ReadPoint(1)
    Cursor.ReadValue("<4i")
    Cursor.ReadPoint(1)
    _, _, UnitCode = Cursor.ReadValue("<HiH")
    Require(UnitCode <= 10, True, "length unit code")


# the surrounding model owns the detail definitions inline before the first pointer
def ReadDetailStart(Cursor):
    Require(Cursor.ReadValue("<H"), (0,), "pre-detail boundary word")
    ReadDetailHead(Cursor)
    ReadCharFormat(Cursor)
    Cursor.ReadValue("<i11d")
    Cursor.ReadValue("<5i2d2i3dIid7i")
    ReadStyleHead(Cursor)
    ReadLengthCode(Cursor)
