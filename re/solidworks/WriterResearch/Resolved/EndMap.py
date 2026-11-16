from struct import pack as PackFields

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor

# the witnessed sketch and blind-boss streams share the empty configuration map
KResolvedCounts = (18, 19)


# the final native count is scoped to the measured modern ordinary configurations
def GuardResolvedEnd(Generation: int, EntryCount: int) -> None:
    RequireArch(Generation, KConfigGen, "modern ordinary resolved list")
    RequireArch(EntryCount in KResolvedCounts, True, "witnessed resolved list shape")


# an empty MBSM map occupies one signed long after the counted feature objects
def EncodeResolvedEnd(*, Generation: int, EntryCount: int) -> bytes:
    GuardResolvedEnd(Generation, EntryCount)
    return PackFields("<i", 0)


# the caller supplies the last feature return so the empty map must reach exact EOF
def ReadResolvedEnd(Cursor: FieldCursor, *, Generation: int, EntryCount: int) -> None:
    GuardResolvedEnd(Generation, EntryCount)
    RequireArch(Cursor.Offset >= 0, True, "valid feature return position")
    RequireArch(len(Cursor.BlobValue) - Cursor.Offset, 4, "final resolved map width")
    RequireArch(Cursor.ReadInts("<i"), (0,), "empty resolved MBSM data map")
