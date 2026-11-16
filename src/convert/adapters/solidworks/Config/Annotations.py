from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Config.Detail import ReadCharFormat, ReadLineWidth
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

# the middle annotation members add only their own scalar fields to the shared base
KAnnotTails = (
    "<3i3di",
    "<6i",
    "<2iH",
    "<2i2d",
)


# the supported base retains an inline font and leaves the layer pointer absent
def ReadAnnotBase(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<id6i")
    RequireArch(Cursor.ReadValue("<h"), (-1,), "annotation settings without a layer")
    for _ in range(2):
        ReadLineWidth(Cursor)
    ReadCharFormat(Cursor)
    _ = Cursor.ReadValue("<i")


# balloon settings interleave property and text names with their scalar options
def ReadBalloonTail(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<6i")
    _ = Cursor.ReadText()
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<I2d2i")
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<3di")


# the document saves these inline members in the order used by the modern serializer
def ReadAnnotDefs(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadValue("<id5iI4i")
    ReadAnnotBase(Cursor)
    ReadBalloonTail(Cursor)
    for Format in KAnnotTails:
        ReadAnnotBase(Cursor)
        _ = Cursor.ReadValue(Format)

    ReadAnnotBase(Cursor)
    _ = Cursor.ReadValue("<i")
    ReadCharFormat(Cursor)

    ReadAnnotBase(Cursor)
    _ = Cursor.ReadValue("<3id")
    ReadAnnotBase(Cursor)
    ReadAnnotBase(Cursor)
    _ = Cursor.ReadPoint(1)
    ReadAnnotBase(Cursor)
    _ = Cursor.ReadValue("<4ididi")
