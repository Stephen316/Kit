"""Read the witnessed modern depth display and its typed length parameter."""

from types import SimpleNamespace

from convert.adapters.solidworks.container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.sketch.DimHandle import KEmptyDimPart as KEmptyDimensionComponent
from convert.adapters.solidworks.sketch.DisplayFields import (
    ReadCache as read_display_cache,
    ReadDisplayTail as read_display_tail,
    ReadNulls as read_nulls,
    ReadPlacement as read_dimension_presentation,
)
from convert.adapters.solidworks.sketch.DisplayOpen import ReadDisplayOpen as read_display_open
from FaceOccurrence import read_transform
from SketchCursor import SketchCursor
from SketchRoot import Require


# the feature handle uses an empty component before the typed dimension object
def read_handle(cursor, pointer_kind):
    offset = cursor.position
    handle = cursor.pointer(pointer_kind, "moFeatureDimHandle_c")
    cursor.null()
    Require(
        cursor.read("<20i"),
        KEmptyDimensionComponent,
        "guarded feature dimension handle component",
    )
    Require(cursor.read("<H"), (0,), "absent handle transform")
    read_nulls(cursor, 4)
    Require(cursor.read("<B"), (0,), "guarded feature handle selector")
    read_nulls(cursor, 2)
    Require(cursor.read("<iHi"), (-1, 0, 0), "guarded feature handle trailer")
    return {"offset": offset, "object_index": handle}


# the model dimension owns the depth value before its display geometry fields
def read_parallel_depth(cursor, pointer_kind):
    offset = cursor.position
    index = cursor.pointer(pointer_kind, "ParallelPlaneDistanceDim_c")
    frame = SimpleNamespace(
        offset=offset,
        Counter=cursor.next_index,
        Classes=cursor.classes,
        Objects=cursor.objects,
    )
    dimension = SketchCursor(cursor.blob, frame, None)
    dim_id, parameter = dimension.ReadDimBasePrefix("moLengthParameter_c")
    name, depth = dimension.Scalars[parameter]
    cursor.position = dimension.Offset
    cursor.next_index = dimension.NextIndex
    cursor.vector(9)
    Require(cursor.read("<H"), (1,), "present parallel dimension vectors")
    cursor.vector(6)
    Require(cursor.read("<H"), (1,), "present parallel dimension transform")
    read_transform(cursor)
    Require(cursor.read("<4H"), (0,) * 4, "empty dimension presentation groups")
    read_dimension_presentation(cursor)
    return {
        "offset": offset,
        "object_index": index,
        "native_dimension_id": dim_id,
        "parameter_object": parameter,
        "parameter_name": name,
        "metres": depth,
        "end": cursor.position,
    }


# saved display copies corroborate the authored parameter before reading the favorite settings
def read_depth_display(cursor, pointer_kind=KDefinitionKind):
    offset = cursor.position
    index = cursor.pointer(KClassRefKind, "moDisplayDistanceDim_c")
    read_display_open(cursor)
    handle = read_handle(cursor, pointer_kind)
    depth = read_parallel_depth(cursor, pointer_kind)
    copies = read_display_cache(cursor)
    Require(copies, (depth["metres"],) * 2, "depth copies agree with parameter")
    favorite = read_display_close(cursor)
    return {
        "offset": offset,
        "object_index": index,
        "handle": handle,
        "dimension": depth,
        "cached_metres": copies,
        "favorite_object": favorite,
        "end": cursor.position,
    }


# the favorite and trailing settings retain their typed nulls and empty text groups
def read_display_close(cursor):
    favorite = cursor.pointer(KClassRefKind, "moFavoriteHandle_c")
    read_display_tail(cursor)
    return favorite
