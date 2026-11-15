"""Close the typed P04 cut sketch after its supporting face has returned."""

from FaceOccurrence import read_transform
from RectangleTail import read_trim_edge, read_trim_surface
from SketchRoot import Require


# the cut sketch materializes two placements and reuses the boss file reference
def read_cut_profile_tail(cursor, cut, boss):
    placement = read_transform(cursor)
    Require(cursor.read("<H"), (1,), "present cut auxiliary transform")
    auxiliary = read_transform(cursor)
    Require(
        (auxiliary["basis"], auxiliary["translation_scale"]),
        (None, (0, 0, 0, 1)),
        "identity cut auxiliary placement",
    )
    Require(cursor.read("<H"), (4,), "guarded cut profile flags")
    cursor.null()
    Require(cursor.read("<2i"), (-1, 0), "guarded cut profile state")
    (state_word,) = cursor.read("<I")
    Require(cursor.read("<H"), (11,), "witnessed cut contour mode")
    cursor.null()
    Require(cursor.read("<H"), (1,), "one cached cut trim surface")
    surface = read_trim_surface(cursor, cut, existing_file=boss["file_ref_object"])
    Require(cursor.read("<H"), (12,), "twelve cached cut trim segments")
    edges = [read_trim_edge(cursor, cut, surface) for _ in range(12)]
    Require(cursor.read("<i"), (0,), "guarded cut profile return state")
    return {
        "placement": placement,
        "auxiliary_placement": auxiliary,
        "state_word": state_word,
        "trim_surface": surface,
        "trim_edges": edges,
        "end": cursor.position,
        "next_map_index": cursor.next_index,
    }
