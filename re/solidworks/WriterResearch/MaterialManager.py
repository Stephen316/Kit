from struct import pack as PackFields

from convert.adapters.solidworks.container.Archive import ArchiveError
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import FieldCursor

# the signed word writes preserve one unsigned counter before the short list count
KEmptyMaterialLayout = "<QH"


# the next offset lets the document resume after the material manager list
def ReadEmptyMaterialManager(BlobValue: bytes, Offset: int) -> tuple[int, int]:
    if Offset < 0:
        raise ArchiveError(f"invalid material manager offset {Offset}")
    Cursor = FieldCursor(BlobValue, Offset)
    Counter, Count = Cursor.ReadInts(KEmptyMaterialLayout)
    RequireArch(Count, 0, "empty material manager list count")
    return Counter, Cursor.Offset


# an empty manager needs only its allocated counter and an empty object list
def EncodeEmptyMaterialManager(Counter: int) -> bytes:
    return PackFields(KEmptyMaterialLayout, Counter, 0)
