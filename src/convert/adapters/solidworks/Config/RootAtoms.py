from convert.adapters.solidworks.Container.Archive import KNullKind, ReadTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor


# the atom body mode distinguishes the supported layout from optional embedded bodies
def AtomEnd(BlobValue: bytes, Offset: int) -> int:
    NameTag = ReadTag(BlobValue, Offset)
    RequireArch(NameTag.kind, KNullKind, "absent atom name")
    Cursor = FieldCursor(BlobValue, Offset + NameTag.size)
    _ = Cursor.ReadInts("<4i")
    _ = Cursor.ReadText()
    RequireArch(Cursor.ReadInts("<i"), (0,), "absent atom child list")
    VisualTag = ReadTag(BlobValue, Cursor.Offset)
    RequireArch(VisualTag.kind, KNullKind, "absent atom visual properties")
    Cursor.Offset += VisualTag.size
    RequireArch(Cursor.ReadInts("<Hi"), (0, 0), "empty atom node list and trailer")
    Fields = Cursor.ReadInts("<13i")
    RequireArch(Fields[5], 0, "supported atom body mode")
    return Cursor.Offset


# the ghost manager must finish every bounded identifier list before its owner continues
def EndGhosts(BlobValue: bytes, Offset: int) -> int:
    Cursor = FieldCursor(BlobValue, Offset)
    _, PackedCount = Cursor.ReadInts("<2I")
    Count = PackedCount & 0x0FFFFFFF
    RequireArch(
        Count <= (len(BlobValue) - Cursor.Offset) // 28, True, "bounded ghost bodies"
    )
    for _ in range(Count):
        *_, Length = Cursor.ReadInts("<5i")
        RequireArch(
            0 <= Length <= (len(BlobValue) - Cursor.Offset - 8) // 4,
            True,
            "bounded ghost body ids",
        )
        for _ in range(Length):
            _ = Cursor.ReadInts("<i")
        RequireArch(Cursor.ReadInts("<2i"), (0, 0), "absent ghost geometry and points")
    return Cursor.Offset
