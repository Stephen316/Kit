"""Follow ordinary resolved rectangles through their saved principal support."""

from ArchiveVersion import KApplicationBuild
from RectangleTail import read_principal_profile_support
from ResolvedPrelude import read_resolved_prelude
from SketchRoot import KGeneration, Require
from convert.adapters.solidworks.Resolved.ContourChain import ReadChainState
from convert.adapters.solidworks.Resolved.ContourTrim import ReadRectEnd, ReadRectTrim
from convert.adapters.solidworks.Resolved.ProfileSketch import ReadProfileBody


# transfer the same map through the inline sketch and back to its containing feature
def read_rectangle_entry(
    blob, config_map, build, has_atom, *, include_coincidence=False
):
    cursor, prelude = read_resolved_prelude(blob, config_map, 19 if has_atom else 18)
    Require(build, KApplicationBuild, "witnessed sketch presentation build")
    previous_events = cursor.PointerEvents
    events = []
    cursor.PointerEvents = events
    try:
        profile = ReadProfileBody(cursor, KGeneration)
    finally:
        cursor.PointerEvents = previous_events
    if previous_events is not None:
        previous_events.extend(events)
    geometry = profile.Geometry
    (coincidence,) = profile.Coincidences
    display = [event for event in events if event[0] >= geometry["geometry_end"]]
    edge_ids = [line["native_id"] for line in geometry["lines"] if line["native_id"] >= 0]
    chain = ReadChainState(cursor, bool(has_atom), edge_ids)
    support = read_principal_profile_support(cursor, prelude["principal_planes"])
    rectangle = {
        "origin": prelude["origin"],
        "name": profile.NameValue,
        "feature_id": profile.FeatureId,
        "profile_offset": profile.Offset,
        "profile_object": profile.ObjectIndex,
        "sketch_offset": profile.SketchOffset,
        "sketch_object": profile.SketchIndex,
        "geometry": geometry,
        "display_pointers": display,
        "chain": chain,
        "support": support,
        "end": cursor.position,
        "next_map_index": cursor.next_index,
    }
    if include_coincidence:
        rectangle["point_coincidence"] = coincidence
    return cursor, rectangle


# the standalone profile modes preserve their established report boundaries
def read_resolved_rectangle(
    blob,
    config_map,
    build,
    has_atom,
    *,
    through_profile=False,
    include_coincidence=False,
):
    cursor, rectangle = read_rectangle_entry(
        blob, config_map, build, has_atom, include_coincidence=include_coincidence
    )
    if through_profile:
        close_rectangle(cursor, rectangle, int(has_atom))
    return rectangle


# the single-profile list finishes at the footer and the body-bearing list begins an extrusion
def close_rectangle(cursor, rectangle, contour_mode):
    geometry = rectangle["geometry"]
    edge_ids = [
        line["native_id"] for line in geometry["lines"] if line["native_id"] >= 0
    ]
    profile = {
        "profile_object": rectangle["profile_object"],
        "native_feature_id": rectangle["feature_id"],
    }
    rectangle["trim"] = ReadRectTrim(cursor, profile, edge_ids, contour_mode)
    following = ReadRectEnd(cursor, bool(contour_mode))
    rectangle["profile_return"] = {
        "offset": cursor.position,
        "next_map_index": cursor.next_index,
        "following": following,
    }
