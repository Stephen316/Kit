"""Read modern document detail settings and inline dimension styles."""

from SketchRoot import Require

# the dimension settings serializer calls its inline members in this order
KStyleTails = (
    "<I2i",  # linear
    "<I",  # angle
    "",  # arc length
    "<Ii",  # radial
    "<I",  # hole callout
    "<iId",  # ordinate
    "<4i2d2i",  # chamfer
    "<iI",  # diameter
    "<iI3i",  # angular ordinate
    "",  # base
)


# each archived string must consume at least its length prefix
def ReadDetailNames(Cursor, Count):
    Require(
        0 <= Count <= len(Cursor.BlobValue) - Cursor.Offset,
        True,
        "bounded detail name count",
    )
    for _ in range(Count):
        Cursor.ReadText()


# the witnessed string arrays use the archive's short count form
def ReadShortNames(Cursor):
    (Count,) = Cursor.ReadValue("<H")
    Require(Count != 0xFFFF, True, "short detail string array count")
    ReadDetailNames(Cursor, Count)


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
    ReadShortNames(Cursor)


# inline character formatting starts with the framed font name
def ReadCharFormat(Cursor):
    Cursor.ReadText()
    Cursor.ReadValue("<didI5dI")


# every style starts with the same base fields and supported no-layer branch
def ReadStyleHead(Cursor):
    Cursor.ReadValue("<3i2di2d2i")
    Cursor.ReadText()
    Cursor.ReadText()
    Cursor.ReadValue("<2d8i")
    Require(Cursor.ReadValue("<h"), (-1,), "dimension style without a layer")
    Cursor.ReadValue("<2iI")


# angle and length units share the scalar layout inherited from moUserUnits_c
def ReadUnitBase(Cursor):
    Cursor.ReadValue("<2i")
    Cursor.ReadPoint(1)
    Cursor.ReadValue("<2i")
    Cursor.ReadPoint(1)
    Cursor.ReadValue("<4i")
    Cursor.ReadPoint(1)
    Cursor.ReadValue("<Hi")


# length unit subclasses read their length code before the optional dual unit pointer
def ReadLengthCode(Cursor):
    ReadUnitBase(Cursor)
    (UnitCode,) = Cursor.ReadValue("<H")
    Require(UnitCode <= 10, True, "length unit code")


# line widths store a mode short and the width in single precision
def ReadLineWidth(Cursor):
    Cursor.ReadValue("<hf")


# the two line fonts inline a modern width before the style code
def ReadLineFont(Cursor):
    Cursor.ReadText()
    ReadLineWidth(Cursor)
    Cursor.ReadValue("<h")


# angle units and appearance fields follow the optional length unit in each style
def ReadStyleTail(Cursor, Format):
    ReadUnitBase(Cursor)
    Cursor.ReadValue("<H")
    ReadCharFormat(Cursor)
    for _ in range(2):
        ReadLineFont(Cursor)
    Cursor.ReadValue("<3i")
    if Format:
        Cursor.ReadValue(Format)


# the surrounding model owns the detail definitions before its ten styles
def ReadDetailStart(Cursor):
    Require(Cursor.ReadValue("<H"), (0,), "pre-detail boundary word")
    ReadDetailHead(Cursor)
    ReadCharFormat(Cursor)
    Cursor.ReadValue("<i11d")
    Cursor.ReadValue("<5i2d2i3dIid7i")
