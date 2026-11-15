"""Follow ordinary resolved rectangles through their saved principal support."""

from types import SimpleNamespace

from ProfileSupport import read_chain
from RectangleTail import read_principal_profile_support, read_rectangle_trim
from ResolvedEntry import read_profile_body_prefix, read_resolved_prelude
from SketchCursor import SketchCursor
from SketchGeom import ReadPointCoincidence
from SketchReader import ReadDisplayFrame, ReadDisplaySteps, ReadGeometry
from SketchRoot import Require
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ReadTag,
)


# the resolved rectangle declares display classes its archive map has yet to allocate
def read_resolved_display(cursor, build, sketch_object, point_ids, dimension_lengths):
    frame = ReadDisplayFrame(build, 1)
    coincidence = ReadPointCoincidence(cursor, point_ids)
    ReadDisplaySteps(
        cursor, frame["steps"], sketch_object, dimension_lengths, Resolved=True
    )
    cursor.AdvanceBytes(frame["trailer_width"])
    return coincidence


# transfer the same map through the inline sketch and back to its containing feature
def read_rectangle_entry(
    blob, config_map, build, has_atom, *, include_coincidence=False
):
    cursor, prelude = read_resolved_prelude(blob, config_map, 19 if has_atom else 18)
    start = cursor.position
    profile = cursor.pointer(KDefinitionKind, "moProfileFeature_c")
    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, feature_id, _ = read_profile_body_prefix(cursor, (0x40000000, 0xC0000000))
    offset = cursor.position
    sketch_object = cursor.pointer(KClassRefKind, "sgSketch")
    archive = SketchCursor(
        blob,
        SimpleNamespace(
            offset=offset,
            Counter=cursor.next_index,
            Classes=cursor.classes,
            Objects=cursor.objects,
        ),
        None,
    )
    geometry = ReadGeometry(archive, sketch_object)
    display = []
    archive.PointerEvents = display
    point_ids = [point["id"] for point in geometry["point_relation_tallies"]]
    coincidence = read_resolved_display(
        archive,
        build,
        sketch_object,
        point_ids,
        [dimension["metres"] for dimension in geometry["length_dimensions"]],
    )
    cursor.position, cursor.next_index = archive.Offset, archive.NextIndex
    count = int(has_atom)
    Require(cursor.read("<Ii"), (count, count), "witnessed rectangle chain state")
    chain = read_chain(cursor, KDefinitionKind) if has_atom else None
    support = read_principal_profile_support(cursor, prelude["principal_planes"])
    Require(
        support["axis"],
        5 - support["native_feature_id"],
        "principal support axis agrees with its plane",
    )
    rectangle = {
        "origin": prelude["origin"],
        "name": name,
        "feature_id": feature_id,
        "profile_offset": start,
        "profile_object": profile,
        "sketch_offset": offset,
        "sketch_object": sketch_object,
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
    if contour_mode:
        Require(
            sorted(rectangle["chain"]["edge_ids"]),
            sorted(edge_ids),
            "body chain covers the sketch perimeter",
        )
    profile = {
        "profile_object": rectangle["profile_object"],
        "native_feature_id": rectangle["feature_id"],
    }
    rectangle["trim"] = read_rectangle_trim(cursor, profile, edge_ids, contour_mode)
    if contour_mode:
        tag = ReadTag(cursor.blob, cursor.position)
        Require(
            (tag.kind, tag.class_name, tag.schema),
            (KDefinitionKind, "moExtrusion_c", 1),
            "next typed extrusion",
        )
        following = "moExtrusion_c"
    else:
        Require(cursor.read("<i"), (0,), "witnessed resolved list footer")
        Require(
            cursor.position, len(cursor.blob), "complete single-profile resolved stream"
        )
        following = "resolved_list_end"
    rectangle["profile_return"] = {
        "offset": cursor.position,
        "next_map_index": cursor.next_index,
        "following": following,
    }
