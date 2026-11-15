"""Read the guarded result body and repeated face choosers of the P04 cut."""

from BossChooser import read_chooser_tail, require_chooser_owner
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
    ReadTag,
)
from FaceOccurrence import (
    read_face_header,
    read_face_tail,
    read_local_component,
    read_surface_id,
)
from SketchRoot import Require

# both modern three integer surface subclasses append fields after the common feature reference
TRIPLE_FIELDS = {
    "moEndFace3IntSurfIdRep_c": (0, 0),
    "moFromSktEnt3IntSurfIdRep_c": (-1, 0),
}


# a result face can reference either the owning cut or the earlier selected boss
def read_result_entity(cursor, boss, cut, allow_cut):
    tag = ReadTag(cursor.blob, cursor.position)
    Require(tag.kind in (KClassRefKind, KDefinitionKind), True, "typed result surface")
    name = tag.class_name or cursor.classes.get(tag.index)
    cut_shape = name in TRIPLE_FIELDS
    Require(
        name in ("moEndFaceSurfIdRep_c", "moFromSktEntSurfIdRep_c")
        or (allow_cut and cut_shape),
        True,
        "witnessed result surface subtype",
    )
    entity = read_surface_id(
        cursor, name, cap=name == "moEndFaceSurfIdRep_c", pointer_kind=tag.kind
    )
    Require(
        entity["file_ref_object"],
        boss["file_ref_object"],
        "reached result file reference",
    )
    if cut_shape:
        Require(
            entity["feature_id"],
            cut["native_feature_id"],
            "result surface belongs to cut",
        )
        extras = cursor.read("<2i")
        Require(extras, TRIPLE_FIELDS[name], "witnessed extra result surface fields")
        entity.update(extra_fields=extras, end=cursor.position)
    else:
        source = boss["choosers"]["caps"][1]["primary"]
        Require(
            (entity["feature_id"], entity["time_word"]),
            (source["feature_id"], source["time_word"]),
            "result surface belongs to reached boss",
        )
    return entity


# counted result faces preserve each representation as a separate typed map object
def read_result_face(cursor, boss, cut, flags):
    header, edge_count = read_face_header(cursor, KClassRefKind, flags)
    entities = [
        read_result_entity(cursor, boss, cut, flags == 768)
        for _ in range(edge_count + 1)
    ]
    read_face_tail(cursor)
    return {**header, "entities": entities, "end": cursor.position}


# the earlier solid body scope retains the only principal result body reference
def read_cut_solid(cursor, boss, cut):
    offset = cursor.position
    body = cursor.pointer(KDefinitionKind, "moCompSolidBody_c")
    unit, part = read_local_component(cursor)
    face = read_result_face(cursor, boss, cut, 0)
    count, body_id, feature_id, first, second = cursor.read("<5i")
    Require((count, first, second), (1, 0, 0), "guarded solid body identifier list")
    Require(feature_id, boss["native_feature_id"], "saved solid body belongs to boss")
    return {
        "offset": offset,
        "object_index": body,
        "unit_component": unit,
        "part_object": part,
        "body_id": body_id,
        "face": face,
        "end": cursor.position,
    }


# later result faces resolve the exact materialized surface objects in the original order
def read_result_alias(cursor, target):
    header, edge_count = read_face_header(cursor, KClassRefKind, 768)
    entries = target["entities"]
    Require(len(entries), edge_count + 1, "same result face entity count")
    aliases = [cursor.pointer(KObjectRefKind, entity["class"]) for entity in entries]
    Require(
        aliases,
        [entity["object_index"] for entity in entries],
        "same result face objects",
    )
    read_face_tail(cursor)
    return {**header, "entity_objects": aliases, "end": cursor.position}


# the cut chooser must preserve both stored result faces and their repeated assembly
def read_cut_choosers(cursor, boss, cut):
    Require(cursor.read("<i2H"), (1, 1, 1), "one first cut chooser item")
    first = cursor.pointer(KClassRefKind, "moPerBodyChooserData_c")
    Require(cursor.read("<H"), (2,), "two cut chooser faces")
    faces = [read_result_face(cursor, boss, cut, 768) for _ in range(2)]
    times = {
        entity["time_word"]
        for face in faces
        for entity in face["entities"]
        if entity["feature_id"] == cut["native_feature_id"]
    }
    Require(len(times), 1, "same authored cut result timestamp")
    bounds = read_chooser_tail(cursor, KClassRefKind, body_ids=())
    require_chooser_owner(cursor, cut, "moICE_c")
    Require(cursor.read("<3H"), (1, 1, 0), "witnessed empty second cut chooser")
    require_chooser_owner(cursor, cut, "moICE_c")
    Require(cursor.read("<i2H"), (1, 1, 1), "one repeated cut chooser item")
    repeated = cursor.pointer(KClassRefKind, "moPerBodyChooserData_c")
    Require(cursor.read("<H"), (2,), "two repeated cut chooser faces")
    aliases = [read_result_alias(cursor, face) for face in faces]
    current = read_chooser_tail(cursor, KClassRefKind, body_ids=())
    Require(
        current["centre_and_scale"],
        bounds["centre_and_scale"],
        "same cut chooser centre",
    )
    require_chooser_owner(cursor, cut, "moICE_c")
    return {
        "primary_object": first,
        "repeated_object": repeated,
        "faces": faces,
        "face_aliases": aliases,
        "centre": bounds,
        "repeated_centre_object": current["centre_object"],
        "end": cursor.position,
    }
