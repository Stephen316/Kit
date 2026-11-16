from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)


# a resolved list can reuse a configuration map only when its saved counter agrees
def OpenResolved(
    BlobValue: bytes, ConfigMap: ArchiveCursor, ExpectedCount: int
) -> ArchiveCursor:
    Header = FieldCursor(BlobValue, 0)
    BaseCount, ListCount = Header.ReadInts("<iH")
    RequireArch(BaseCount, ConfigMap.NextIndex, "derived configuration map counter")
    RequireArch(ListCount, ExpectedCount, "witnessed short resolved list")
    return ArchiveCursor(
        BlobValue,
        Header.Offset,
        ConfigMap.NextIndex,
        ConfigMap.Classes.copy(),
        ConfigMap.Objects.copy(),
    )
