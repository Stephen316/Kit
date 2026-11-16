from struct import pack as PackFields

from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# default datums have no source atoms or transfer arrays
KAtomOpening = (0, 0, 0, 0, 0)


# the empty plane keeps its body chooser flag despite having no kernel atom
KAtomOptions = (0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0)


# read the empty standalone attachment grammar before reading geometry from the plane
def ReadPrincipalAtom(Cursor: ArchiveCursor) -> None:
    RequireArch(Cursor.ReadInts("<i"), (0,), "ordinary model feature state")
    RequireArch(Cursor.ReadInts("<3H2i"), KAtomOpening, "empty plane atom lists")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<4i3Hi2Hi"), KAtomOptions, "empty plane atom controls")
    RequireArch(
        Cursor.ReadInts("<2i"), (0, 1), "absent actions and local partition record"
    )
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<13i"), (0,) * 13, "empty local plane atom maps")


# field widths and null pointers preserve a datum without introducing a kernel body
def WritePrincipalAtom(Writer: ArchiveWriter) -> None:
    Writer.i32(0)
    Writer.raw(PackFields("<3H2i", *KAtomOpening))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<4i3Hi2Hi", *KAtomOptions))
    Writer.i32(0)
    Writer.i32(1)
    Writer.raw(EncodeNull())
    for _ in range(13):
        Writer.i32(0)
