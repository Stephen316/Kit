from convert.adapters.solidworks.config.RootEntry import EntryStop
from convert.adapters.solidworks.container.Archive import KNullKind, ReadTag
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import FieldCursor


# pair counts must fit before the caller can locate the next native boundary
def ReadKeyPairs(Cursor: FieldCursor, Count: int) -> None:
    RequireArch(
        0 <= Count <= (len(Cursor.BlobValue) - Cursor.Offset) // 8,
        True,
        "bounded native key pairs",
    )
    for _ in range(Count):
        _ = Cursor.ReadInts("<2i")


# unsupported optional root objects would move the material and its later allocations
def FindMaterial(BlobValue: bytes, Offset: int) -> int:
    Cursor = FieldCursor(BlobValue, Offset)
    (BoxPresent,) = Cursor.ReadInts("<B")
    RequireArch(BoxPresent in (0, 1), True, "bounding box presence")
    if BoxPresent:
        _ = Cursor.ReadPoint(10)
    Fields = Cursor.ReadValue("<6I2dI")
    RequireArch(
        (Fields[1], Fields[5], Fields[-1]),
        (0, 0, 2),
        "root optional lists and record selector",
    )
    RequireArch(
        Cursor.ReadValue("<H2I"), (0, 0xAAAAAAAA, 0xBBBBBBBB), "empty inline alias map"
    )
    RequireArch(Cursor.ReadInts("<I"), (0,), "absent dynamic array")
    _, Shrink, Defeature, _ = Cursor.ReadInts("<4I")
    RequireArch((Shrink, Defeature), (0, 0), "absent shrink wrap and defeature")
    Count, _, Notes = Cursor.ReadInts("<H2I")
    RequireArch((Count, Notes), (0, 0), "empty inline objects and notes")
    _ = Cursor.ReadValue("<16si16s3i")
    Imported, _, _, _, Count = Cursor.ReadInts("<5I")
    RequireArch(Imported, 0, "absent import metadata")
    ReadKeyPairs(Cursor, Count)
    CacheTag = ReadTag(BlobValue, Cursor.Offset)
    RequireArch(CacheTag.kind, KNullKind, "absent publish cache")
    RequireArch(
        ReadTag(BlobValue, Cursor.Offset + CacheTag.size).class_name,
        "gcXhatch_c",
        "typed hatch boundary",
    )
    return Cursor.Offset


# both saved split lengths must agree with the body fields before entering the atom list
def ModelAtomStart(BlobValue: bytes, ModelEntry: EntryStop) -> tuple[int, int, int]:
    ModelBody = ModelEntry.offset + ReadTag(BlobValue, ModelEntry.offset).size
    SceneTag = ReadTag(BlobValue, ModelBody)
    RequireArch(SceneTag.kind, KNullKind, "absent model scene")
    Cursor = FieldCursor(BlobValue, ModelBody + SceneTag.size)
    _ = Cursor.ReadInts("<i")
    BodyStart = Cursor.Offset
    RequireArch(Cursor.ReadInts("<2i"), (0, 0), "empty body visualization groups")
    _, _, _, _, KeyCount = Cursor.ReadInts("<5I")
    ReadKeyPairs(Cursor, KeyCount)
    Split = Cursor.Offset
    RootHeader = FieldCursor(BlobValue, ReadTag(BlobValue, 0).size)
    (FirstLength,) = RootHeader.ReadInts("<I")
    RequireArch(Split, RootHeader.Offset + FirstLength, "first split end")
    (SecondLength,) = Cursor.ReadInts("<I")
    RequireArch(Cursor.Offset + SecondLength, len(BlobValue), "second split end")
    RequireArch(Cursor.ReadInts("<Hi"), (0, 0), "empty root feature list")
    _, AtomCount = Cursor.ReadInts("<2i")
    return BodyStart, Cursor.Offset, AtomCount
