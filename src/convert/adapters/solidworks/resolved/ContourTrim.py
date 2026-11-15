from collections.abc import Sequence
from typing import Literal, TypedDict

from convert.adapters.solidworks.container.Archive import KDefinitionKind, ReadTag
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.ContourSurf import (
    KContourEdge,
    ProfileOwner,
    ReadContourEdge,
    ReadTrimSurface,
    TrimSurface,
)


# profile closure must retain the contour surface and its four owned trim segments
class RectangleTrim(TypedDict):
    state_word: int
    trim_surface: TrimSurface
    trim_edges: list[KContourEdge]
    end: int


# a rectangle trim may complete only when its edge identities cover the saved perimeter
def ReadRectTrim(
    Cursor: ArchiveCursor, Owner: ProfileOwner, EdgeIds: Sequence[int], ContourMode: int
) -> RectangleTrim:
    RequireArch(ContourMode in (0, 1), True, "supported rectangle contour mode")
    RequireArch(Cursor.ReadInts("<2H"), (0, 4), "guarded rectangle profile flags")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<2i"), (-1, 0), "guarded rectangle profile state")
    (StateWord,) = Cursor.ReadInts("<I")
    RequireArch(
        Cursor.ReadInts("<H"), (ContourMode,), "witnessed rectangle contour mode"
    )
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<H"), (1,), "one cached trim surface")
    Surface = ReadTrimSurface(Cursor, Owner)
    RequireArch(Cursor.ReadInts("<H"), (4,), "four cached trim segments")
    Edges = [ReadContourEdge(Cursor, Owner, Surface) for _ in range(4)]
    RequireArch(
        sorted(Segment["edge_id"] for Segment in Edges),
        sorted(EdgeIds),
        "trim cache covers the saved rectangle edges",
    )
    RequireArch(Cursor.ReadInts("<i"), (0,), "guarded profile return state")
    return {
        "state_word": StateWord,
        "trim_surface": Surface,
        "trim_edges": Edges,
        "end": Cursor.Offset,
    }


# the part must either close its resolved list or reach the typed extrusion body
def ReadRectEnd(
    Cursor: ArchiveCursor, HasAtom: bool
) -> Literal["moExtrusion_c", "resolved_list_end"]:
    if HasAtom:
        TagValue = ReadTag(Cursor.BlobValue, Cursor.Offset)
        RequireArch(
            (TagValue.kind, TagValue.class_name, TagValue.schema),
            (KDefinitionKind, "moExtrusion_c", 1),
            "next typed extrusion",
        )
        return "moExtrusion_c"
    RequireArch(Cursor.ReadInts("<i"), (0,), "witnessed resolved list footer")
    RequireArch(
        Cursor.Offset, len(Cursor.BlobValue), "complete single-profile resolved stream"
    )
    return "resolved_list_end"
