from convert.adapters.solidworks.container.Archive import KClassRefKind
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.sketch.Cursor import SketchArchive
from convert.adapters.solidworks.sketch.Displays import TakeShownClass
from convert.adapters.solidworks.sketch.GeometryTypes import SketchLine


# inactive sketch settings must remain empty before the region can allocate
def ReadRegionStart(Cursor: SketchArchive) -> None:
    RequireArch(Cursor.ReadInts("<7H"), (0,) * 7, "empty post-display collections")
    ModeValue, Flags, State = Cursor.ReadInts("<2Hi")
    RequireArch(ModeValue in (1, 2), True, "witnessed sketch presentation mode")
    RequireArch(Flags, 1, "guarded sketch presentation flags")
    RequireArch(State in (5, 9), True, "witnessed sketch state")
    RequireArch(
        Cursor.ReadInts("<15i"),
        (6, 5, *([1] * 11), 0, 1),
        "guarded sketch environment settings",
    )
    RequireArch(Cursor.ReadInts("<4H"), (0,) * 4, "empty additional sketch arrays")
    RequireArch(Cursor.ReadText(), "", "empty sketch line style name")
    RequireArch(
        Cursor.ReadValue("<Hf3i"),
        (65535, -1, -1, 1, -1),
        "guarded sketch line settings",
    )
    RequireArch(Cursor.ReadPoint(3), (0, 0, 0), "empty sketch presentation point")
    _ = Cursor.ReadInts("<I")
    RequireArch(Cursor.ReadInts("<2i"), (1, 0), "guarded sketch presentation flags")
    RequireArch(Cursor.ReadInts("<2H5i"), (0,) * 7, "empty remaining pre-region fields")


# region edge handles must point into the current sketch regardless of list order
def ReadOutline(Cursor: SketchArchive, Count: int) -> list[int]:
    Outline: list[int] = []
    for _ in range(Count):
        _, _, Handle = Cursor.TakePointer(("sgLineHandle",), KClassRefKind)
        Cursor.ReadPayload("sgLineHandle", Handle)
        NativeId, Owner, Flags = Cursor.Handles[Handle]
        RequireArch((Owner, Flags), (-1, 0), "local region boundary handle")
        Outline.append(NativeId)
    return Outline


# perimeter order is accepted only when it closes a cycle over the actual saved lines
def ReadRegion(Cursor: SketchArchive, Lines: list[SketchLine]) -> None:
    _ = Cursor.TakePointer(("suObList",), KClassRefKind)
    RequireArch(Cursor.ReadInts("<H"), (1,), "one witnessed closed sketch region")
    TakeShownClass(Cursor, "moSketchRegion_c")
    _ = Cursor.TakePointer(("suObList",), KClassRefKind)
    Edges = {
        LineRow["native_id"]: set(LineRow["point_indices"])
        for LineRow in Lines
        if LineRow["native_id"] >= 0
    }
    (Count,) = Cursor.ReadInts("<H")
    RequireArch(
        (Count, len(Edges)), (4, 4), "one handle for each rectangular region edge"
    )
    Outline = ReadOutline(Cursor, Count)
    RequireArch(
        sorted(Outline), sorted(Edges), "region owns the entire saved perimeter"
    )
    RequireArch(
        all(
            len(Edges[First] & Edges[NextValue]) == 1
            for First, NextValue in zip(Outline, Outline[1:] + Outline[:1], strict=True)
        ),
        True,
        "saved region boundary forms a continuous cycle",
    )
