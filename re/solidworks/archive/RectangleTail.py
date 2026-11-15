"""Read the modern P04 rectangle profile through its principal support and trim cache."""

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
    ReadTag,
)
from convert.adapters.solidworks.resolved.ProfilePlane import CheckProfileRef, ReadProfileRef
from FileReference import read_file_reference
from ProfileSupport import read_chain
from SketchRoot import KGeneration, Require


# the modern surface and boundary records must both refer to the owning profile
def require_profile_owner(cursor, profile):
    owner = cursor.pointer(KObjectRefKind, "moProfileFeature_c")
    Require(owner, profile["profile_object"], "trim belongs to the current profile")


# the contour surface is the first owner to materialize the saved document reference
def read_trim_surface(cursor, profile, existing_file=None):
    kind = KDefinitionKind if existing_file is None else KClassRefKind
    index = cursor.pointer(kind, "moSimpleSurfIdRep_c")
    require_profile_owner(cursor, profile)
    feature_ref_class = (
        cursor.next_index
        if kind == KDefinitionKind
        else ReadTag(cursor.blob, cursor.position).index
    )
    feature_ref = cursor.pointer(kind, "moFR_c")
    if existing_file is None:
        file_ref = read_file_reference(cursor)
    else:
        object_index = cursor.pointer(KObjectRefKind, "moExtObject_c")
        Require(object_index, existing_file, "contour uses the reached file reference")
        file_ref = {"object_index": object_index}
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


# corner placement is valid only when its typed frame and saved datum agree
def read_principal_profile_support(cursor, planes):
    reference = ReadProfileRef(cursor, KGeneration)
    plane = next(
        (item for item in planes if item["native_feature_id"] == reference.FeatureId),
        None,
    )
    Require(plane is not None, True, "support resolves an earlier principal plane")
    plane_data = plane["plane_data"]
    CheckProfileRef(reference, plane_data["point_metres"], plane_data["normal_world"])
    return {
        "offset": reference.Offset,
        "object_index": reference.ObjectIndex,
        "unit_component": reference.UnitIndex,
        "part_object": reference.PartIndex,
        "plane_name": plane["name"],
        "plane_object": plane["object_index"],
        "native_feature_id": reference.FeatureId,
        "native_time_word": reference.TimeValue,
        "axis": reference.AxisCode,
        "transform": {
            "basis": reference.BasisValue,
            "translation_scale": reference.ShiftScale,
        },
    }


# profile completion materializes the file and edge references needed by the downstream map
def read_rectangle_trim(cursor, profile, edge_ids, contour_mode):
    Require(cursor.read("<2H"), (0, 4), "guarded rectangle profile flags")
    cursor.null()
    Require(cursor.read("<2i"), (-1, 0), "guarded rectangle profile state")
    (state_word,) = cursor.read("<I")
    Require(cursor.read("<H"), (contour_mode,), "witnessed rectangle contour mode")
    cursor.null()
    Require(cursor.read("<H"), (1,), "one cached trim surface")
    surface = read_trim_surface(cursor, profile)
    Require(cursor.read("<H"), (4,), "four cached trim segments")
    edges = [read_trim_edge(cursor, profile, surface) for _ in range(4)]
    Require(
        sorted(edge["edge_id"] for edge in edges),
        sorted(edge_ids),
        "trim cache covers the saved rectangle edges",
    )
    Require(cursor.read("<i"), (0,), "guarded profile return state")
    return {
        "state_word": state_word,
        "trim_surface": surface,
        "trim_edges": edges,
        "end": cursor.position,
    }


# P04 derives the expected profile contour directly from its saved sketch chain
def read_rectangle_tail(cursor, profile, planes):
    Require(cursor.read("<Ii"), (1, 1), "one modern profile chain")
    chain = read_chain(cursor, KDefinitionKind)
    support = read_principal_profile_support(cursor, planes)
    return {
        "chain": chain,
        "support": support,
        **read_rectangle_trim(cursor, profile, chain["edge_ids"], 1),
    }
