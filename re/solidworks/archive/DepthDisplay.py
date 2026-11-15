"""Read the witnessed modern depth display and its typed length parameter."""

from types import SimpleNamespace

from convert.adapters.solidworks.container.Archive import KClassRefKind, KDefinitionKind
from FaceOccurrence import FaceCursor, read_transform
from FileReference import read_text
from SketchCursor import KEmptyDimensionComponent, SketchCursor
from SketchRoot import KGeneration, Require


# archive nulls preserve the choice of an empty optional object without moving the map
def read_nulls(cursor, count):
    for _ in range(count):
        cursor.null()


# even empty display labels must use the native string framing before the next field
def read_empty_strings(cursor, count):
    for _ in range(count):
        Require(read_text(cursor), "", "empty depth display label")


# sketch dimensions and feature depth share the display base serialization
def read_display_open(cursor, *, sketch=False):
    Require(cursor.read("<H"), (0,), "witnessed display opening")
    read_nulls(cursor, 3)
    visual = cursor.read("<2i2HBIHhf2Hi")
    Require(
        visual[:-1],
        (0, 0, 65535, 0, 3, 0xFFFFFFFF, 0, 0, -1, 0, 0),
        "guarded display visual properties",
    )
    Require(
        visual[-1] in (range(10, 16) if sketch else (0,)),
        True,
        "witnessed display visual index",
    )
    cursor.null()
    Require(
        cursor.read("<4i3d2i"),
        (0, KGeneration, 0, 524416, 0, 0, 0, 0, 0),
        "guarded display model fields",
    )
    cursor.null()
    Require(cursor.vector(3), (0, 0, 0), "empty display reference point")
    transform = read_transform(cursor)
    Require(
        (transform["basis"], transform["translation_scale"]),
        (None, (0, 0, 0, 1)),
        "identity display setup",
    )
    Require(
        cursor.read("<2iBd2i"),
        (1, 200 if sketch else 201, 0, 0, 0, 0),
        "guarded display mode",
    )
    cursor.null()
    style = cursor.read("<d2ihf2ihf8ihf5i")
    Require(style[-5:], (0, 0, 0, 0, 4), "guarded display appearance mode")
    Require(cursor.vector(12), (0,) * 12, "empty saved display positions")
    Require(cursor.read("<i"), (2,), "guarded display direction count")
    cursor.vector(6)
    read_empty_strings(cursor, 1)
    position = cursor.vector(3)
    if not sketch:
        Require(position, (0, 0, 0), "guarded feature depth placement")
    Require(cursor.read("<i"), (18,), "guarded distance display kind")
    cursor.null()
    setup = cursor.read("<i4d4i2diH3id2i")
    Require(setup[11:16], (0, 0, 0, 0, 0), "empty depth display additions")
    Require(setup[-2:], (0, 1), "guarded depth handle route")


# sketch display reads record pointer events from the same archive cursor and map
def sketch_display_window(cursor):
    return FaceCursor(
        cursor.BlobValue,
        cursor.Offset,
        cursor.NextIndex,
        cursor.Classes,
        cursor.Objects,
        null_events=cursor.PointerEvents,
    )


# the display base reads null children before either archive map allocates the typed handle
def read_sketch_display_open(cursor):
    window = sketch_display_window(cursor)
    read_display_open(window, sketch=True)
    cursor.Offset = window.position


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


# both distance display forms retain the same framed labels and numerical placement values
def read_dimension_presentation(cursor):
    read_empty_strings(cursor, 4)
    cursor.vector(22)
    cursor.read("<i7H")
    cursor.vector(3)


# the pair of saved values follows the common post-dimension display fields
def read_display_cache(cursor):
    read_nulls(cursor, 2)
    post = cursor.read("<2d2i2HI2i")
    Require(post[-2:], (0, 0), "empty post dimension object arrays")
    read_empty_strings(cursor, 1)
    read_nulls(cursor, 2)
    state, cached, *settings, placement = cursor.read("<id4Id")
    Require(
        (state, tuple(settings)), (-1, (8, 16, 1, 1)), "guarded depth display cache"
    )
    read_empty_strings(cursor, 1)
    return cached, placement


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


# sketch handles already own the dimension, so only its presentation and cached values follow
def read_sketch_display_close(cursor, metres, favorite_kind):
    window = sketch_display_window(cursor)
    Require(window.read("<3H"), (0,) * 3, "empty sketch dimension presentation groups")
    read_dimension_presentation(window)
    copies = read_display_cache(window)
    Require(
        all(abs(value - metres) <= 1e-9 for value in copies),
        True,
        "sketch dimension display copies agree with the owned parameter",
    )
    cursor.Offset = window.position
    cursor.TakePointer(("moFavoriteHandle_c",), favorite_kind)
    window.position = cursor.Offset
    window.next_index = cursor.NextIndex
    read_display_tail(window)
    cursor.Offset = window.position


# favorite data uses the same framed strings and guarded child list across distance displays
def read_display_tail(cursor):
    appearance = cursor.read("<2iId2HI4didHi30Id")
    Require(appearance[:6], (0, -1, 0, -1, 1, 1), "guarded depth favorite style")
    read_empty_strings(cursor, 4)
    cursor.read("<2HiI")
    read_nulls(cursor, 3)
    Require(cursor.read("<I"), (1002101,), "guarded saved depth display flags")
    read_nulls(cursor, 2)
    Require(cursor.read("<3i"), (0, 0, 0), "empty additional depth display items")
    cursor.null()
    cursor.read("<5id6i")
    read_empty_strings(cursor, 2)
    cursor.read("<3i")
    read_empty_strings(cursor, 1)
    cursor.read("<2i3d2i")
    read_empty_strings(cursor, 1)
    cursor.read("<i5di")
    cursor.null()
    Require(cursor.read("<i"), (0,), "guarded distance display return")
