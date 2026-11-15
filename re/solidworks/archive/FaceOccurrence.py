"""Read the witnessed modern face occurrence and its enclosing reference plane."""

from math import isclose

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    KObjectRefKind,
)
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.LocalFrame import ReadLocalPart, ReadLocalPose
from SketchRoot import KGeneration, Require


# the witnessed chain begins with already established archive class and object ownership
class FaceCursor(ArchiveCursor):
    def __init__(self, blob, position, next_index, classes, objects, null_events=None):
        super().__init__(blob, position, next_index, classes, objects)
        self.null_events = null_events

    @property
    def blob(self):
        return self.BlobValue

    @property
    def position(self):
        return self.Offset

    @position.setter
    def position(self, value):
        self.Offset = value

    @property
    def next_index(self):
        return self.NextIndex

    @next_index.setter
    def next_index(self, value):
        self.NextIndex = value

    @property
    def classes(self):
        return self.Classes

    @property
    def objects(self):
        return self.Objects

    read = ArchiveCursor.ReadValue
    vector = ArchiveCursor.ReadPoint

    # face and resolved records use the witnessed compact tag branch
    def pointer(self, kind, name=None):
        _, _, index = self.TakePointer((name,), kind, CompactOnly=True)
        return index

    # a null child chooses the witnessed branch without inventing an object map entry
    def null(self):
        if self.null_events is not None:
            self.null_events.append(
                (self.position, self.next_index, KNullKind, None, 0)
            )
        self.pointer(KNullKind)

# a surface identifier is usable only when its typed feature reference resolves ownership
def read_surface_id(cursor, kind, cap=False, pointer_kind=KClassRefKind):
    offset = cursor.position
    index = cursor.pointer(pointer_kind, kind)
    cursor.null()
    feature_ref = cursor.pointer(KClassRefKind, "moFR_c")
    file_ref = cursor.pointer(KObjectRefKind, "moExtObject_c")
    feature_id, time_word = cursor.read("<iI")
    (occurrence,) = cursor.read("<i")
    if cap:
        Require(occurrence in (0, 1), True, "recognized end face occurrence")
        Require(cursor.read("<i"), (0,), "supported extra end face selector")
    return {
        "offset": offset,
        "end": cursor.position,
        "class": kind,
        "object_index": index,
        "feature_ref_object": feature_ref,
        "file_ref_object": file_ref,
        "feature_id": feature_id,
        "time_word": time_word,
        "occurrence": occurrence,
    }


# body chooser and component faces share the same checked entity envelope
def read_face_header(cursor, pointer_kind, expected_flags):
    offset = cursor.position
    index = cursor.pointer(pointer_kind, "moFaceRef_c")
    body = cursor.position
    first, second, count = cursor.read("<3I")
    Require((first, second, count), (1, 0, 6), "witnessed face kind and entity count")
    flags, classifier = cursor.read("<iI")
    Require(flags, expected_flags, "witnessed face reference flags")
    cursor.vector(2)
    cursor.null()  # moVertexRef_c
    return {
        "offset": offset,
        "body": body,
        "object_index": index,
        "classifier": classifier,
    }, count - 2


# the trailing endpoint remains typed even when its optional reference is empty
def read_face_tail(cursor):
    cursor.null()  # final empty entity identity
    Require(
        cursor.read("<5I"), (0, 0, KGeneration, 0, 0), "modern face reference trailer"
    )


# the bounded local face branch preserves its primary cap and ordered sketch edge identities
def read_face_occurrence(cursor):
    header, edge_count = read_face_header(cursor, KClassRefKind, 512)
    cap = read_surface_id(cursor, "moEndFaceSurfIdRep_c", cap=True)
    edges = [
        read_surface_id(cursor, "moFromSktEntSurfIdRep_c") for _ in range(edge_count)
    ]
    read_face_tail(cursor)
    for edge in edges:
        for key in ("feature_id", "time_word", "file_ref_object"):
            Require(edge[key], cap[key], f"same face source {key}")
    return {
        **header,
        "end": cursor.position,
        "primary": cap,
        "ordered_edges": edges,
    }


# the archive stores the optional basis independently of the point and unit normal
def read_transform(cursor):
    basis, translation_scale = ReadLocalPose(cursor)
    return {"basis": basis, "translation_scale": translation_scale}


# the saved plane geometry independently corroborates the bound cap orientation
def read_plane_data(cursor):
    root = cursor.vector(3)
    normal = cursor.vector(3)
    Require(
        isclose(sum(value * value for value in normal), 1), True, "unit plane normal"
    )
    transform = read_transform(cursor)
    border = cursor.vector(4)
    cursor.null()  # moCompEdge_c
    cursor.read("<3iB2i")
    Require(cursor.read("<H"), (0,), "absent extra plane payload")
    for _ in range(3):
        cursor.null()  # facet reference, axis, sketch entity
    return {
        "root_metres": root,
        "normal_world": normal,
        "transform": transform,
        "border_metres": border,
    }


# both local support components must establish the same containing part ownership
def read_local_component(cursor):
    return ReadLocalPart(cursor, KGeneration)


# the nested local component must point to the archived part before its entity reference
def read_component_face(cursor):
    offset = cursor.position
    component = cursor.pointer(KDefinitionKind, "moCompFace_c")
    unit, part = read_local_component(cursor)
    Require(cursor.read("<B"), (0,), "absent face alias")
    occurrence = read_face_occurrence(cursor)
    cursor.null()  # modern optional moExtObject_c
    return {
        "offset": offset,
        "object_index": component,
        "unit_component": unit,
        "part_object": part,
        "occurrence": occurrence,
    }


# the enclosing wrapper repeats the point and normal within the same support allocation
def close_plane_data(cursor, plane):
    Require(cursor.read("<H"), (1,), "local reference wrapper mode")
    cursor.null()  # moComponent_c
    cursor.read("<2i")
    Require(cursor.read("<2H"), (0, 0), "absent reference wrapper transforms")
    cursor.read("<11i")
    cursor.vector(4)
    Require(cursor.vector(3), plane["root_metres"], "same wrapper root point")
    Require(cursor.vector(3), plane["normal_world"], "same wrapper normal")
    read_transform(cursor)
    cursor.vector(3)
    cursor.null()  # moDisplayDim_c
    first, second, backed_geometry, last = cursor.read("<4i")
    Require(
        (first, second, backed_geometry, last),
        (0, 1, 0, 0),
        "guarded face plane trailer",
    )


# the nested callback must finish at the verified enclosing support return
def read_face_data(cursor):
    index = cursor.pointer(KDefinitionKind, "moFaceRefPlnData_c")
    plane = read_plane_data(cursor)
    component = read_component_face(cursor)
    close_plane_data(cursor, plane)
    Require(cursor.read("<i"), (0,), "face-based component plane axis code")
    return {
        "plane_data_object": index,
        "support_end": cursor.position,
        "next_map_index": cursor.next_index,
        "plane": plane,
        "component": component,
    }
