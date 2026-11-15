from convert.adapters.solidworks.config.RootLayout import KConfigGen
from convert.adapters.solidworks.container.Archive import KObjectRefKind
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor

# display handles share a component layout with no external owner or transform
KEmptyDimPart = (0,) * 10 + (-1,) * 4 + (0,) * 5 + (KConfigGen,)


# reference wrappers can only continue when both optional transforms are absent
def ReadRefTail(Cursor: ArchiveCursor) -> None:
    _ = Cursor.ReadInts("<H")
    Cursor.ReadNull()
    _ = Cursor.ReadInts("<2i")
    RequireArch(Cursor.ReadInts("<2H"), (0, 0), "absent reference transforms")
    _ = Cursor.ReadInts("<11i")


# dimension handles reuse the same fields before either kind of sketch ownership
def ReadDimRoute(Cursor: ArchiveCursor) -> tuple[int, int, int]:
    RequireArch(Cursor.ReadInts("<H"), (0,), "absent dimension transform")
    for _ in range(4):
        Cursor.ReadNull()
    (Selector,) = Cursor.ReadInts("<B")
    Cursor.ReadNull()
    Cursor.ReadNull()
    (State,) = Cursor.ReadInts("<i")
    RequireArch(Cursor.ReadInts("<H"), (0,), "absent second dimension transform")
    (Flags,) = Cursor.ReadInts("<i")
    return Selector, State, Flags


# a display handle must point to its current sketch before exposing a dimension slot
def ReadDimHandle(Cursor: ArchiveCursor, SketchObject: int) -> int:
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<20i"), KEmptyDimPart, "empty display handle component"
    )
    RequireArch(ReadDimRoute(Cursor), (0, -1, 0), "local display handle state")
    _, _, Owner = Cursor.TakePointer(("sgSketch",), KObjectRefKind)
    RequireArch(Owner, SketchObject, "display handle owns its sketch")
    (DimSlot,) = Cursor.ReadInts("<i")
    return DimSlot
