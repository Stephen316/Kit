"""Read the guarded P04 boss chooser bodies and their saved cap references."""

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
)
from FaceOccurrence import read_face_header, read_face_tail, read_surface_id
from SketchRoot import Require


# both cap occurrences must carry the actual rectangle file reference and boss identity
def read_cap(cursor, pointer_kind, occurrence, boss):
    face, count = read_face_header(cursor, pointer_kind, 768)
    Require(face["classifier"], 0, "guarded chooser face classifier")
    primary = read_surface_id(
        cursor, "moEndFaceSurfIdRep_c", cap=True, pointer_kind=pointer_kind
    )
    boundary_class = "moFromSktEntSurfIdRep_c"
    edges = [read_surface_id(cursor, boundary_class, pointer_kind=pointer_kind)]
    edges.extend(read_surface_id(cursor, boundary_class) for _ in range(count - 1))
    Require(primary["occurrence"], occurrence, "saved chooser cap occurrence")
    for entity in [primary, *edges]:
        Require(
            (entity["file_ref_object"], entity["feature_id"], entity["time_word"]),
            (boss["file_ref_object"], boss["native_feature_id"], primary["time_word"]),
            "same saved boss face source",
        )
    read_face_tail(cursor)
    return {**face, "end": cursor.position, "primary": primary, "edges": edges}


# the repeated chooser faces must select the materialized cap and edge objects
def read_cap_alias(cursor, target):
    face, count = read_face_header(cursor, KClassRefKind, 768)
    Require(face["classifier"], 0, "guarded chooser face classifier")
    cap = cursor.pointer(KObjectRefKind, "moEndFaceSurfIdRep_c")
    edges = [
        cursor.pointer(KObjectRefKind, "moFromSktEntSurfIdRep_c") for _ in range(count)
    ]
    Require(cap, target["primary"]["object_index"], "same chooser cap object")
    Require(
        edges,
        [edge["object_index"] for edge in target["edges"]],
        "same chooser edge objects",
    )
    read_face_tail(cursor)
    return {**face, "end": cursor.position, "cap_object": cap, "edge_objects": edges}


# the chooser centre and counted arrays close the record with an exact map counter
def read_chooser_tail(cursor, pointer_kind):
    Require(cursor.read("<2H"), (0, 1), "empty secondary chooser and one centre")
    centre_object = cursor.pointer(pointer_kind, "moBBoxCenterData_c")
    Require(cursor.read("<i"), (1,), "witnessed bounding centre type")
    centre = cursor.vector(4)
    Require(cursor.read("<2iHIi"), (0, 0, 1, 0, 0), "guarded body chooser state")
    return {"centre_object": centre_object, "centre_and_scale": centre}


# each inline chooser refers back to the extrusion that allocated it
def require_chooser_owner(cursor, boss):
    index = cursor.pointer(KObjectRefKind, "moExtrusion_c")
    Require(index, boss["object_index"], "chooser owner is the current boss")


# materialization and replay of the same cap identities establish chooser ownership
def read_boss_choosers(cursor, boss):
    Require(cursor.read("<2H"), (1, 1), "one primary body chooser item")
    first = cursor.pointer(KDefinitionKind, "moPerBodyChooserData_c")
    Require(cursor.read("<H"), (2,), "two primary chooser caps")
    caps = [
        read_cap(cursor, KDefinitionKind, 0, boss),
        read_cap(cursor, KClassRefKind, 1, boss),
    ]
    bounds = read_chooser_tail(cursor, KDefinitionKind)
    require_chooser_owner(cursor, boss)
    Require(cursor.read("<3H"), (1, 1, 0), "witnessed empty second chooser")
    require_chooser_owner(cursor, boss)
    Require(cursor.read("<i2H"), (1, 1, 1), "one repeated body chooser item")
    second = cursor.pointer(KClassRefKind, "moPerBodyChooserData_c")
    Require(cursor.read("<H"), (2,), "two repeated chooser caps")
    aliases = [read_cap_alias(cursor, cap) for cap in caps]
    repeated = read_chooser_tail(cursor, KClassRefKind)
    Require(
        repeated["centre_and_scale"], bounds["centre_and_scale"], "same chooser centre"
    )
    require_chooser_owner(cursor, boss)
    return {
        "primary_object": first,
        "repeated_object": second,
        "caps": caps,
        "cap_aliases": aliases,
        "centre": bounds,
        "repeated_centre_object": repeated["centre_object"],
        "end": cursor.position,
    }
