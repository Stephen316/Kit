from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

# the dimension settings serializer calls its inline members in this order
KStyleTails = (
    "<I2i",
    "<I",
    "",
    "<Ii",
    "<I",
    "<iId",
    "<4i2d2i",
    "<iI",
    "<iI3i",
    "",
)


# each archived string must consume at least its length prefix
def ReadDetailNames(Cursor: ArchiveCursor, Count: int) -> None:
    RequireArch(
        0 <= Count <= len(Cursor.BlobValue) - Cursor.Offset,
        True,
        "bounded detail name count",
    )
    for _ in range(Count):
        _ = Cursor.ReadText()


# the witnessed string arrays use the archives short count form
def ReadShortNames(Cursor: ArchiveCursor) -> None:
    (Count,) = Cursor.ReadInts("<H")
    RequireArch(Count != 0xFFFF, True, "short detail string array count")
    ReadDetailNames(Cursor, Count)


# modern detail definitions store exclusions before two groups of fixed scalar rows
def ReadDetailHead(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<i")
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<dBIid5Bi")
    for _ in range(2):
        _ = Cursor.ReadValue("<3I3d")
    _ = Cursor.ReadValue("<i2d9i")
    _ = Cursor.ReadValue("<B4i2B2h2idi")
    for _ in range(2):
        _ = Cursor.ReadText()
        _ = Cursor.ReadValue("<i")
    _ = Cursor.ReadValue("<12i")
    (ExclusionCount,) = Cursor.ReadInts("<i")
    ReadDetailNames(Cursor, ExclusionCount)
    _ = Cursor.ReadValue("<3i")
    for _ in range(6):
        _ = Cursor.ReadValue("<8i")
    ReadShortNames(Cursor)


# inline character formatting starts with the framed font name
def ReadCharFormat(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<didI5dI")


# every style starts with the same base fields and supported nolayer branch
def ReadStyleHead(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<3i2di2d2i")
    _ = Cursor.ReadText()
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<2d8i")
    RequireArch(Cursor.ReadValue("<h"), (-1,), "dimension style without a layer")
    _ = Cursor.ReadValue("<2iI")


# angle and length units share the scalar layout inherited from mouserunitsc
def ReadUnitBase(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<2i")
    _ = Cursor.ReadPoint(1)
    _ = Cursor.ReadValue("<2i")
    _ = Cursor.ReadPoint(1)
    _ = Cursor.ReadValue("<4i")
    _ = Cursor.ReadPoint(1)
    _ = Cursor.ReadValue("<Hi")


# length unit subclasses read their length code before the optional dual unit pointer
def ReadLengthCode(Cursor: ArchiveCursor) -> None:
    ReadUnitBase(Cursor)
    (UnitCode,) = Cursor.ReadInts("<H")
    RequireArch(UnitCode <= 10, True, "length unit code")


# line widths store a mode short and the width in single precision
def ReadLineWidth(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<hf")


# the two line fonts inline a modern width before the style code
def ReadLineFont(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadText()
    ReadLineWidth(Cursor)
    _ = Cursor.ReadValue("<h")


# angle units and appearance fields follow the optional length unit in each style
def ReadStyleTail(Cursor: ArchiveCursor, Format: str) -> None:
    ReadUnitBase(Cursor)
    _ = Cursor.ReadValue("<H")
    ReadCharFormat(Cursor)
    for _ in range(2):
        ReadLineFont(Cursor)
    _ = Cursor.ReadValue("<3i")
    if Format:
        _ = Cursor.ReadValue(Format)


# the surrounding model owns the detail definitions before its ten styles
def ReadDetailStart(Cursor: ArchiveCursor) -> None:
    RequireArch(
        Cursor.ReadValue("<H"), (0,), "empty model array before detail settings"
    )
    ReadDetailHead(Cursor)
    ReadCharFormat(Cursor)
    _ = Cursor.ReadValue("<i11d")
    _ = Cursor.ReadValue("<5i2d2i3dIid7i")
