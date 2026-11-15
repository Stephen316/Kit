"""Follow ordinary resolved rectangles through their saved principal support."""

from struct import unpack_from
from types import SimpleNamespace

from ConfigMap import ReadPointer
from ProfileSupport import read_chain
from RectangleTail import read_principal_profile_support
from ResolvedEntry import read_profile_body_prefix, read_resolved_prelude
from SketchCursor import SketchCursor
from SketchReader import ReadDisplayFrame, ReadGeometry
from SketchRoot import Require
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    KObjectRefKind,
)

DISPLAY_CLASSES = (
    "moDisplayDistanceDim_c",
    "moSkDimHandleValG2_c",
    "moFavoriteHandle_c",
    "moSketchRegion_c",
)


# the resolved rectangle declares display classes its archive map has yet to allocate
def read_resolved_display(cursor, build, sketch_object):
    frame = ReadDisplayFrame(build, 1)
    prefix = frame["inline_prefix"]
    Require(cursor.ReadValue("<3H"), tuple(prefix[:3]), "inline relation presentation")
    events = []
    ReadPointer(cursor, events, KNullKind)
    ReadPointer(cursor, events, KNullKind)
    Require(cursor.ReadValue("<2H"), tuple(prefix[5:]), "inline relation trailer")
    for width, kind, name, *count in frame["steps"]:
        cursor.AdvanceBytes(width)
        if name in DISPLAY_CLASSES and name not in cursor.Classes.values():
            kind = KDefinitionKind
        ReadPointer(cursor, events, kind, name)
        if count:
            (observed,) = unpack_from("<H", cursor.BlobValue, cursor.Offset)
            Require(observed, count[0], "witnessed display list count")
        if kind == KObjectRefKind and name == "sgSketch":
            Require(events[-1][-1], sketch_object, "display handle owns the resolved sketch")
    cursor.AdvanceBytes(frame["trailer_width"])
    return events


# transfer the same map through the inline sketch and back to its containing feature
def read_resolved_rectangle(blob, config_map, build, has_atom):
    cursor, prelude = read_resolved_prelude(blob, config_map, 19 if has_atom else 18)
    start = cursor.position
    profile = cursor.pointer(KDefinitionKind, "moProfileFeature_c")
    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, feature_id, _ = read_profile_body_prefix(cursor, (0x40000000, 0xC0000000))
    offset = cursor.position
    sketch_object = cursor.pointer(KClassRefKind, "sgSketch")
    archive = SketchCursor(
        blob,
        SimpleNamespace(offset=offset, Counter=cursor.next_index, Classes=cursor.classes, Objects=cursor.objects),
        None,
    )
    geometry = ReadGeometry(archive, sketch_object)
    display = read_resolved_display(archive, build, sketch_object)
    cursor.position, cursor.next_index = archive.Offset, archive.NextIndex
    count = int(has_atom)
    Require(cursor.read("<Ii"), (count, count), "witnessed rectangle chain state")
    chain = read_chain(cursor, KDefinitionKind) if has_atom else None
    support = read_principal_profile_support(cursor, prelude["principal_planes"])
    Require(support["axis"], 5 - support["native_feature_id"], "principal support axis agrees with its plane")
    return {
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
