from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.NamedNode import ReadNamedFeat


# the named feature and empty early reference locate the owned sketch tag
def ReadProfileHead(
    Cursor: ArchiveCursor, ExpectedFlags: tuple[int, ...]
) -> tuple[str, int, int]:
    NameValue, FeatureId = ReadNamedFeat(Cursor, ExpectedFlags)
    _ = Cursor.ReadInts("<i")
    RequireArch(
        Cursor.ReadInts("<i"), (0,), "guarded scalar before early profile pointer"
    )
    EarlyOffset = Cursor.Offset
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<i"), (0,), "guarded scalar after early profile pointer"
    )
    return NameValue, FeatureId, EarlyOffset
