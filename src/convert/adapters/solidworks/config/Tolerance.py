from collections.abc import Callable

from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.config.AnnotationData import ReadAnnoHelper
from convert.adapters.solidworks.config.Detail import (
    ReadCharFormat,
    ReadDetailNames,
    ReadShortNames,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch


# each counted frame ends with two typed tolerance pointers before any indicators
def ReadTolFrame(Cursor: ArchiveCursor, ReadNull: Callable[[], object]) -> None:
    _ = Cursor.ReadText()
    for _ in range(2):
        _ = Cursor.ReadValue("<B")
        ReadDetailNames(Cursor, 2)
    for _ in range(6):
        ReadShortNames(Cursor)
    _ = Cursor.ReadValue("<2i")
    RequireArch(Cursor.ReadValue("<H"), (0,), "tolerance frame without datum records")
    _ = ReadNull()
    _ = ReadNull()
    RequireArch(Cursor.ReadCount(), 0, "empty tolerance indicator list")


# the helper is inline but delegates its nullable tolerance children to the map reader
def ReadTolData(Cursor: ArchiveCursor, ReadNull: Callable[[], object]) -> None:
    for _ in range(Cursor.ReadCount()):
        ReadTolFrame(Cursor, ReadNull)
    _ = Cursor.ReadValue("<2i")
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<4BiB")
    for _ in range(2):
        ReadDetailNames(Cursor, 2)
        _ = Cursor.ReadValue("<B")
    _ = Cursor.ReadText()
    _ = Cursor.ReadValue("<4B")
    ReadCharFormat(Cursor)
    ReadAnnoHelper(Cursor)
    _ = Cursor.ReadValue("<6B")
