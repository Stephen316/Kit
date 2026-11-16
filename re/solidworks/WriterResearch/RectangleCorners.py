from dataclasses import dataclass as Dataclass
from math import isfinite as IsFinite
from struct import pack as PackFields

from AuthoredProfile import KSketchClass
from PartArchive import PartArchiveWriter
from SketchMemberStyle import COLOR_STATUS_TYPE, Weight, default_visual, standard_width
from convert.adapters.solidworks.Container.Archive import KBigObjectTag, EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KLineHandle = "sgLineHandle"
KCornerMask = 0x1E
KMemberStatus = 2


# contour handles refer to short entity identities in the owning sketch
@Dataclass(frozen=True, slots=True)
class CornerPoint:
    Identity: int
    Position: tuple[float, float]
    RelationCount: int


# derive each saved pair from the complete rectangle rather than from file offsets
def ContourPairs(
    Corners: tuple[CornerPoint, ...], Lines: dict[int, tuple[int, int]]
) -> tuple[tuple[int, ...], ...]:
    RequireArch(len(Corners), 4, "ordinary rectangle corner count")
    RequireArch(set(Lines), set(range(1, 5)), "ordinary short perimeter identities")
    Coords = tuple(Corner.Position for Corner in Corners)
    RequireArch(
        all(len(Point) == 2 and all(map(IsFinite, Point)) for Point in Coords)
        and len(set(Coords)) == 4
        and all(len({Point[Axis] for Point in Coords}) == 2 for Axis in (0, 1)),
        True,
        "nondegenerate axis-aligned local rectangle",
    )
    AllEdges = {
        frozenset((First, Second))
        for First in range(len(Coords))
        for Second in range(First + 1, len(Coords))
        if any(Coords[First][Axis] == Coords[Second][Axis] for Axis in (0, 1))
    }
    RequireArch(
        {frozenset(Edge) for Edge in Lines.values()},
        AllEdges,
        "complete local perimeter",
    )
    return tuple(
        tuple(sorted(Line for Line, Edge in Lines.items() if Slot in Edge))
        for Slot in range(len(Corners))
    )


# inline corner content precedes two distinct handle allocations and an empty sharp tail
def WriteCorner(
    Writer: PartArchiveWriter,
    Point: CornerPoint,
    Handles: tuple[int, ...],
    Mask: int,
    Status: int,
) -> None:
    Writer.raw(PackFields("<H2i", 0, 0, Point.Identity))
    Writer.raw(default_visual())
    Writer.raw(PackFields("<iH", Point.RelationCount, 0))
    # the native ordinary constraint-color branch maps status 2 to color 4
    Writer.raw(COLOR_STATUS_TYPE.pack(4, Status, 1))
    Writer.raw(standard_width(Weight.THIN))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<2Hi", 4, 0, 0))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<Bd2I", 0, 1.0, 0, 0))
    Writer.raw(PackFields("<H2d2H", Mask, *Point.Position, 0, len(Handles)))
    for Handle in Handles:
        Writer.BeginObject(KLineHandle, 1)
        Writer.raw(PackFields("<H2i", Handle, -1, 0))
    Writer.raw(PackFields("<Hi4d2H", 0, -2, 0.0, 0.0, 0.0, 0.0, 0, 0))


# validate the graph and the current owner before mutating the shared archive
def WriteRectCorners(
    Writer: PartArchiveWriter,
    Generation: int,
    Sketch: int,
    Corners: tuple[CornerPoint, ...],
    Lines: dict[int, tuple[int, int]],
    *,
    Mask: int,
    Status: int,
) -> None:
    RequireArch(Generation, 19000, "ordinary rectangle corner generation")
    RequireArch(
        (Mask, Status), (KCornerMask, KMemberStatus), "bounded solved corner branch"
    )
    RequireArch(
        Writer.next_index == Sketch + 1
        and Writer.objects.get(Sketch) == KSketchClass
        and KLineHandle not in Writer.classes
        and Writer.next_index <= KBigObjectTag - 9,
        True,
        "current sketch owns its first compact line handle allocation",
    )
    RequireArch(
        tuple(Point.Identity for Point in Corners), (1, 2, 3, 4), "corner creation IDs"
    )
    RequireArch(
        all(
            type(Point.RelationCount) is int and 0 <= Point.RelationCount <= 3
            for Point in Corners
        ),
        True,
        "ordinary corner relation incidences",
    )
    for Corner, Handles in zip(Corners, ContourPairs(Corners, Lines), strict=True):
        WriteCorner(Writer, Corner, Handles, Mask, Status)
