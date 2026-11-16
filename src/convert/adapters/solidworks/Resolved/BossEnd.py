from typing import TypedDict

from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.BossDepth import DepthDisplay, ReadBossDepth


# the saved end specification determines one signed direction and its termination
class EndSpec(TypedDict):
    offset: int
    object_index: int
    single_end: int
    flip: int
    direction: int
    conditions: tuple[int, int]


# the blind end points to its depth display before the end record continues
class BlindEnd(EndSpec):
    depth_dimension_offset: int
    depth_dimension_class: int


# successful closure retains the complete display and exact feature boundary
class BossClose(TypedDict):
    depth_display: DepthDisplay
    from_end_object: int
    end: int


# supported operations may expose only the single end route with no direction reference
def ReadEndHead(
    Cursor: ArchiveCursor, KindValue: str, Directions: tuple[int, ...] = (0,)
) -> EndSpec:
    Offset = Cursor.Offset
    _, _, SpecValue = Cursor.TakePointer(("moEndSpec_c",), KindValue, CompactOnly=True)
    Cursor.ReadNull()
    Single, FlipValue, Direction = Cursor.ReadInts("<3i")
    RequireArch((Single, FlipValue), (1, 0), "witnessed single extrusion direction")
    RequireArch(Direction in Directions, True, "witnessed extrusion direction")
    Cursor.ReadNull()
    First, Second = Cursor.ReadInts("<2i")
    return {
        "offset": Offset,
        "object_index": SpecValue,
        "single_end": Single,
        "flip": FlipValue,
        "direction": Direction,
        "conditions": (First, Second),
    }


# both termination slots must agree with the blind layout before reading the display
def ReadBlindEnd(Cursor: ArchiveCursor, Directions: tuple[int, ...]) -> BlindEnd:
    SpecValue = ReadEndHead(Cursor, KDefinitionKind, Directions)
    RequireArch(SpecValue["conditions"], (0, 0), "witnessed blind end conditions")
    TagValue = ReadTag(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        (TagValue.kind, Cursor.Classes.get(TagValue.index)),
        (KClassRefKind, "moDisplayDistanceDim_c"),
        "typed depth display boundary",
    )
    return {
        **SpecValue,
        "depth_dimension_offset": Cursor.Offset,
        "depth_dimension_class": TagValue.index,
    }


# the empty draft and surface fields lead to a typed start record
def ReadStartHead(Cursor: ArchiveCursor, KindValue: str, State: int) -> int:
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadValue("<BHBHd6i"),
        (1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0),
        "guarded empty end surface and draft fields",
    )
    Cursor.ReadNull()
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<4i2H3i"),
        (0,) * 6 + (State, 0, 0),
        "guarded end feature fields",
    )
    _, _, Origin = Cursor.TakePointer(("moFromEndSpec_c",), KindValue, CompactOnly=True)
    return Origin


# the ordinary blind boss starts from its sketch plane
def ReadEndTail(Cursor: ArchiveCursor, KindValue: str, State: int) -> int:
    Origin = ReadStartHead(Cursor, KindValue, State)
    RequireArch(Cursor.ReadInts("<i"), (0,), "extrusion starts from its sketch plane")
    _ = Cursor.ReadInts("<5i")
    return Origin


# the modeled depth and the starting plane record must both finish before the feature returns
def ReadBossClose(Cursor: ArchiveCursor) -> BossClose:
    Depth = ReadBossDepth(Cursor)
    Origin = ReadEndTail(Cursor, KDefinitionKind, 0)
    RequireArch(Cursor.ReadValue("<di"), (0, -1), "guarded extrusion return state")
    return {"depth_display": Depth, "from_end_object": Origin, "end": Cursor.Offset}
