"""Walk the guarded generation-19000 Origin sketch and feature suffix."""

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ReadString,
)
from FaceOccurrence import read_local_component, read_transform
from SketchRoot import Require


# the origin uses empty presentation lists but still allocates both objects
def read_empty_list(cursor):
    offset = cursor.position
    index = cursor.pointer(KClassRefKind, "suObList")
    Require(cursor.read("<H"), (0,), "empty origin presentation list")
    return {"offset": offset, "object_index": index, "end": cursor.position}


# typed historical fields constrain the modern branch between the two list allocations
def read_presentation(cursor):
    Require(cursor.read("<7H"), (0,) * 7, "empty origin inline presentation")
    first = read_empty_list(cursor)
    Require(cursor.read("<7H"), (0,) * 7, "guarded origin presentation counters")
    Require(cursor.read("<HHi"), (2, 1, 2), "modern origin sketch state")
    Require(cursor.read("<15i"), (2,) + (1,) * 12 + (0, 1), "bent reference array")
    Require(cursor.read("<4H"), (0,) * 4, "empty origin auxiliary groups")
    label, width = ReadString(cursor.blob, cursor.position)
    Require((label, width), ("", 4), "empty wide origin presentation label")
    cursor.position += width
    Require(cursor.read("<hf3i"), (-1, -1.0, -1, 1, -1), "default origin display")
    Require(cursor.vector(3), (0, 0, 0), "origin display vector")
    Require(cursor.read("<I2i"), (1, 0, 0), "guarded origin display state")
    Require(cursor.read("<2H5i"), (0,) * 7, "empty origin display arrays")
    second = read_empty_list(cursor)
    Require(cursor.read("<H7i"), (0,) * 8, "empty origin region trailer")
    Require(cursor.read("<Ii"), (0, 0), "empty origin profile chain")
    Require(cursor.read("<iB"), (3, 1), "absent origin kernel packet")
    Require(cursor.read("<iH2IH"), (0, 0, 0, 100000, 0), "empty origin profile maps")
    return {"lists": [first, second], "sketch_end": cursor.position}


# the origin points to a local principal feature instead of embedding its own plane
def read_feature_tail(cursor):
    cursor.null()
    support_offset = cursor.position
    support = cursor.pointer(KDefinitionKind, "moCompRefPlane_c")
    unit, part = read_local_component(cursor)
    feature_id, time_word = cursor.read("<iI")
    cursor.null()
    Require(cursor.read("<i"), (3,), "guarded origin plane direction state")
    transform = read_transform(cursor)
    Require(
        (transform["basis"], transform["translation_scale"]),
        (None, (0, 0, 0, 1)),
        "origin identity placement",
    )
    Require(cursor.read("<2H"), (0, 4), "guarded origin outer flags")
    cursor.null()
    marker, auxiliary, state_word, count = cursor.read("<2iIH")
    Require((marker, auxiliary, count), (-7, 0, 0), "modern origin feature trailer")
    cursor.null()
    Require(cursor.read("<2Hi"), (0, 0, 0), "empty origin final groups")
    return {
        "support": {
            "offset": support_offset,
            "object_index": support,
            "unit_component": unit,
            "part_object": part,
            "native_feature_id": feature_id,
            "native_time_word": time_word,
        },
        "feature_state_word": state_word,
    }
