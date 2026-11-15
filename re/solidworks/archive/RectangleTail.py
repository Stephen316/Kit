"""Read the modern P04 rectangle profile through its principal support and trim cache."""

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
    ReadTag,
)
from FaceOccurrence import read_local_component, read_transform
from FileReference import read_file_reference
from ProfileSupport import read_chain
from SketchRoot import Require


# the modern surface and boundary records must both refer to the owning profile
def require_profile_owner(cursor, profile):
    owner = cursor.pointer(KObjectRefKind, "moProfileFeature_c")
    Require(owner, profile["profile_object"], "trim belongs to the current profile")


# the contour surface is the first owner to materialize the saved document reference
def read_trim_surface(cursor, profile):
    index = cursor.pointer(KDefinitionKind, "moSimpleSurfIdRep_c")
    require_profile_owner(cursor, profile)
    feature_ref_class = cursor.next_index
    feature_ref = cursor.pointer(KDefinitionKind, "moFR_c")
    file_ref = read_file_reference(cursor)
    feature_id, time_word, occurrence = cursor.read("<iIi")
    Require(feature_id, profile["native_feature_id"], "contour feature ownership")
    Require(occurrence, 0, "witnessed first contour occurrence")
    return {
        "object_index": index,
        "feature_ref_class": feature_ref_class,
        "feature_ref_object": feature_ref,
        "file_reference": file_ref,
        "feature_id": feature_id,
        "time_word": time_word,
        "occurrence": occurrence,
    }


# each trim segment must preserve the contour surface reference in the same archive map
def read_trim_edge(cursor, profile, surface):
    tag = ReadTag(cursor.blob, cursor.position)
    Require(tag.kind in (KDefinitionKind, KClassRefKind), True, "typed trim segment")
    class_name = tag.class_name or cursor.classes.get(tag.index)
    Require(
        class_name in ("moSegmLeftTrimEdgeIdRep_c", "moSegmRightTrimEdgeIdRep_c"),
        True,
        "witnessed trim segment type",
    )
    index = cursor.pointer(tag.kind, class_name)
    require_profile_owner(cursor, profile)
    cursor.pointer(KClassRefKind, "moFR_c")
    file_ref = cursor.pointer(KObjectRefKind, "moExtObject_c")
    feature_id, time_word, edge_id, extra = cursor.read("<iI2i")
    Require(
        (file_ref, feature_id, time_word, extra),
        (
            surface["file_reference"]["object_index"],
            surface["feature_id"],
            surface["time_word"],
            0,
        ),
        "same contour document and feature reference",
    )
    return {"object_index": index, "class": class_name, "edge_id": edge_id}


# ordinary sketch profiles can resolve their principal support without embedded face data
def read_principal_support(cursor, planes):
    offset = cursor.position
    index = cursor.pointer(KClassRefKind, "moCompRefPlane_c")
    unit, part = read_local_component(cursor)
    feature_id, time_word = cursor.read("<iI")
    plane = next(
        (item for item in planes if item["native_feature_id"] == feature_id), None
    )
    Require(plane is not None, True, "support resolves an earlier principal plane")
    cursor.null()
    (axis,) = cursor.read("<i")
    Require(axis in (1, 3), True, "witnessed principal support axes")
    return {
        "offset": offset,
        "object_index": index,
        "unit_component": unit,
        "part_object": part,
        "plane_name": plane["name"],
        "plane_object": plane["object_index"],
        "native_feature_id": feature_id,
        "native_time_word": time_word,
        "axis": axis,
        "transform": read_transform(cursor),
    }


# profile completion must include the counted trim records that build the downstream map
def read_rectangle_tail(cursor, profile, planes):
    Require(cursor.read("<Ii"), (1, 1), "one modern profile chain")
    chain = read_chain(cursor, KDefinitionKind)
    Require(cursor.read("<iB"), (3, 1), "absent rectangle kernel packet")
    Require(cursor.read("<iHI"), (0, 0, 0), "empty rectangle edge tables")
    Require(cursor.read("<IH"), (100000, 0), "empty rectangle contour map")
    cursor.null()
    support = read_principal_support(cursor, planes)
    Require(cursor.read("<2H"), (0, 4), "guarded rectangle profile flags")
    cursor.null()
    Require(cursor.read("<2i"), (-1, 0), "guarded rectangle profile state")
    (state_word,) = cursor.read("<I")
    Require(cursor.read("<H"), (1,), "witnessed rectangle contour mode")
    cursor.null()
    Require(cursor.read("<H"), (1,), "one cached trim surface")
    surface = read_trim_surface(cursor, profile)
    Require(cursor.read("<H"), (4,), "four cached trim segments")
    edges = [read_trim_edge(cursor, profile, surface) for _ in range(4)]
    Require(
        sorted(edge["edge_id"] for edge in edges),
        sorted(chain["edge_ids"]),
        "trim cache covers the saved chain edges",
    )
    Require(cursor.read("<i"), (0,), "guarded profile return state")
    return {
        "chain": chain,
        "support": support,
        "state_word": state_word,
        "trim_surface": surface,
        "trim_edges": edges,
        "end": cursor.position,
    }
