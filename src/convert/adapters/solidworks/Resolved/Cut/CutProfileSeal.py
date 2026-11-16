from typing import TypedDict

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.ContourSurf import (
    KContourEdge,
    ProfileOwner,
    ReadContourEdge,
    ReadTrimSurface,
    TrimSurface,
)

from convert.adapters.solidworks.Resolved.Support.FaceFrame import (
    FacePose,
    ReadFacePose,
)


# the terminal profile cache retains its actual authored placement and contour boundaries
class CutProfileSeal(TypedDict):
    placement: FacePose
    auxiliary_placement: FacePose
    state_word: int
    trim_surface: TrimSurface
    trim_edges: list[KContourEdge]
    end: int
    next_map_index: int


# the cut profile reuses the earlier part reference after both placements
def ReadCutSeal(
    Cursor: ArchiveCursor,
    Profile: ProfileOwner,
    FileObject: int,
) -> CutProfileSeal:
    Placement = ReadFacePose(Cursor)
    RequireArch(Cursor.ReadInts("<H"), (1,), "present cut auxiliary transform")
    Auxiliary = ReadFacePose(Cursor)
    RequireArch(
        (Auxiliary["basis"], Auxiliary["translation_scale"]),
        (None, (0, 0, 0, 1)),
        "identity cut auxiliary placement",
    )
    RequireArch(Cursor.ReadInts("<H"), (4,), "guarded cut profile flags")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<2i"), (-1, 0), "guarded cut profile state")
    (State,) = Cursor.ReadInts("<I")
    RequireArch(Cursor.ReadInts("<H"), (11,), "witnessed cut contour mode")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<H"), (1,), "one cached cut trim surface")
    Surface = ReadTrimSurface(Cursor, Profile, FileObject)
    RequireArch(Cursor.ReadInts("<H"), (12,), "twelve cached cut trim segments")
    Edges = [ReadContourEdge(Cursor, Profile, Surface) for _ in range(12)]
    RequireArch(Cursor.ReadInts("<i"), (0,), "guarded cut profile return state")
    return {
        "placement": Placement,
        "auxiliary_placement": Auxiliary,
        "state_word": State,
        "trim_surface": Surface,
        "trim_edges": Edges,
        "end": Cursor.Offset,
        "next_map_index": Cursor.NextIndex,
    }
