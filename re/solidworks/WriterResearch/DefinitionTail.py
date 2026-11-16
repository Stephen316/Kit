from struct import pack as PackFields
from typing import cast as CastValue

from convert.adapters.solidworks.container.Archive import ArchiveError
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import FieldCursor


# the measured part generations put different base fields before the terminal double
def HasVariabilityCount(Generation: int) -> bool:
    if Generation not in (18000, 19000):
        raise ArchiveError(f"unsupported part Definition tail generation {Generation}")
    return Generation == 19000


# the caller must locate the tail before checking its fields and stream end
def ReadPartDefinitionTail(BlobValue: bytes, Offset: int, Generation: int) -> float:
    HasCount = HasVariabilityCount(Generation)
    if Offset < 0:
        raise ArchiveError(f"invalid part Definition tail offset {Offset}")
    Cursor = FieldCursor(BlobValue, Offset)
    if HasCount:
        RequireArch(Cursor.ReadInts("<i"), (0,), "empty Definition variability count")
    (TerminalValue,) = Cursor.ReadValue("<d")
    RequireArch(Cursor.Offset, len(BlobValue), "part Definition tail end")
    return CastValue(float, TerminalValue)


# the empty base vector and caller supplied double are enough to construct the tail
def EncodePartDefinitionTail(Generation: int, TerminalValue: float) -> bytes:
    if HasVariabilityCount(Generation):
        return PackFields("<id", 0, TerminalValue)
    return PackFields("<d", TerminalValue)
