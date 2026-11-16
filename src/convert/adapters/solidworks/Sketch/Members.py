from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.GeometryTypes import KLineRow, KPointRow


# point and line members share their identity and display fields before geometry
def ReadMember(Cursor: SketchArchive) -> tuple[int, int, int, int, int, int]:
    Index, Identity = Cursor.ReadInts("<2i")
    _ = Cursor.ReadValue("<HHBIHhf")
    RelationTally, Compact = Cursor.ReadInts("<iH")
    if not Compact:
        _ = Cursor.ReadValue("<3Hhf")
    External = Cursor.ReadObject(None, "sgExtEnt_c")
    Flags, FlagsTwo, _ = Cursor.ReadInts("<2Hi")
    if not Compact:
        _ = Cursor.ReadObject(None)
    RequireArch(Cursor.ReadInts("<B"), (0,), "absent member name")
    _ = Cursor.ReadValue("<d2I")
    return Index, Identity, Flags, FlagsTwo, RelationTally, External


# a point proxy must keep the native reference that accompanies its coordinates
def ReadPointMut(Cursor: SketchArchive) -> KPointRow:
    (Subtype,) = Cursor.ReadInts("<H")
    RequireArch(Subtype in (0, 1), True, "supported sketch point subtype")
    _, Identity, _, _, RelationTally, External = ReadMember(Cursor)
    if External:
        Cursor.PointReferences[Identity] = Cursor.SketchReferences[External]
    (Flags,) = Cursor.ReadInts("<H")
    RequireArch(bool(Flags & 0x10), True, "2D sketch point")
    Coords = Cursor.ReadPoint(2)
    _ = Cursor.ReadInts("<2H")
    if not Flags & 0x20:
        _ = Cursor.ReadObject(None, "sgLineHandle")
        _ = Cursor.ReadObject(None, "sgLineHandle")
    _ = Cursor.ReadInts("<H")
    if not Flags & 0x20:
        _ = Cursor.ReadInts("<i")
        _ = Cursor.ReadPoint(2)
        _ = Cursor.ReadPoint(2)
    RequireArch(Cursor.ReadInts("<H"), (0,), "absent point jet")
    _ = Cursor.ReadInts("<H")
    return Identity, RelationTally, Coords


# the extended slot form still must name a point from this sketch
def ReadPointSlot(Cursor: SketchArchive) -> int:
    (SlotValue,) = Cursor.ReadInts("<H")
    if SlotValue == 0xFFFF:
        (SlotValue,) = Cursor.ReadInts("<i")
    return SlotValue


# connectivity must follow saved point slots independently of serialized line order
def ReadLineItem(Cursor: SketchArchive, PointCount: int) -> KLineRow:
    RequireArch(Cursor.ReadInts("<H"), (0,), "supported inline line mode")
    Index, Identity, Flags, FlagsTwo, _, External = ReadMember(Cursor)
    RequireArch(External, 0, "absent inline line proxy")
    FirstPoint = ReadPointSlot(Cursor)
    SecondPoint = ReadPointSlot(Cursor)
    _ = Cursor.ReadInts("<2H")
    _ = Cursor.ReadPoint(1)
    if FlagsTwo & 0x200:
        _ = Cursor.ReadPoint(3)
    _ = Cursor.ReadInts("<H")
    RequireArch(
        all(0 <= Endpoint < PointCount for Endpoint in (FirstPoint, SecondPoint)),
        True,
        "valid inline line point indices",
    )
    return Index, Identity, Flags, FirstPoint, SecondPoint
