"""Read the witnessed modern face occurrence and its enclosing reference plane."""

from dataclasses import dataclass
from math import isclose, isfinite
from struct import calcsize, unpack_from

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    KObjectRefKind,
    ReadTag,
)
from SketchRoot import KGeneration, Require


# the witnessed chain begins with already established archive class and object ownership
@dataclass
class FaceCursor:
    blob: bytes
    position: int
    next_index: int
    classes: dict[int, str]
    objects: dict[int, str]

    # compact native fields advance one shared cursor through enclosing object scopes
    def read(self, format):
        fields = unpack_from(format, self.blob, self.position)
        self.position += calcsize(format)
        return fields

    # same kind lookups rule out resolving class tokens against unrelated objects
    def pointer(self, kind, name=None):
        start = self.position
        tag = ReadTag(self.blob, start)
        Require(tag.kind, kind, f"archive pointer kind at {start}")
        Require(tag.wide, False, f"compact archive pointer at {start}")
        self.position += tag.size
        if kind == KNullKind:
            return 0
        if kind == KObjectRefKind:
            Require(self.objects.get(tag.index), name, f"object type at {start}")
            return tag.index
        if kind == KDefinitionKind:
            Require(
                (tag.schema, tag.class_name), (1, name), f"class definition at {start}"
            )
            self.allocate(self.classes, name)
        else:
            Require(self.classes.get(tag.index), name, f"class ownership at {start}")
        return self.allocate(self.objects, name)

    # class definitions and materialized objects advance the same archive counter
    def allocate(self, table, name):
        index = self.next_index
        Require(
            index not in self.classes and index not in self.objects,
            True,
            "unused map index",
        )
        table[index] = name
        self.next_index += 1
        return index

    # a null child chooses the witnessed branch without inventing an object map entry
    def null(self):
        self.pointer(KNullKind)

    # all vector results must be finite before they can be compared to observed geometry
    def vector(self, count):
        values = self.read(f"<{count}d")
        Require(all(map(isfinite, values)), True, "finite geometry")
        return values


# a surface identifier is usable only when its typed feature reference resolves ownership
def read_surface_id(cursor, kind, cap=False):
    offset = cursor.position
    index = cursor.pointer(KClassRefKind, kind)
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


# the bounded local face branch preserves its primary cap and ordered sketch edge identities
def read_face_occurrence(cursor):
    offset = cursor.position
    index = cursor.pointer(KClassRefKind, "moFaceRef_c")
    body = cursor.position
    first, second, count = cursor.read("<3I")
    Require((first, second, count), (1, 0, 6), "witnessed face kind and entity count")
    flags, classifier = cursor.read("<iI")
    Require(flags, 512, "witnessed face reference flags")
    cursor.vector(2)
    cursor.null()  # moVertexRef_c
    cap = read_surface_id(cursor, "moEndFaceSurfIdRep_c", cap=True)
    edges = [
        read_surface_id(cursor, "moFromSktEntSurfIdRep_c") for _ in range(count - 2)
    ]
    cursor.null()  # final empty entity identity
    Require(
        cursor.read("<5I"), (0, 0, KGeneration, 0, 0), "modern face reference trailer"
    )
    for edge in edges:
        for key in ("feature_id", "time_word", "file_ref_object"):
            Require(edge[key], cap[key], f"same face source {key}")
    return {
        "offset": offset,
        "body": body,
        "end": cursor.position,
        "object_index": index,
        "classifier": classifier,
        "primary": cap,
        "ordered_edges": edges,
    }


# the archive stores the optional basis independently of the point and unit normal
def read_transform(cursor):
    (flag,) = cursor.read("<B")
    Require(flag in (0, 1), True, "transform basis selector")
    basis = cursor.vector(9) if flag else None
    translation_scale = cursor.vector(4)
    Require(cursor.read("<B"), (0,), "absent nested transform")
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


# the nested local component must point to the archived part before its entity reference
def read_component_face(cursor):
    offset = cursor.position
    component = cursor.pointer(KDefinitionKind, "moCompFace_c")
    unit = cursor.pointer(KClassRefKind, "moUnitComponent_c")
    part = cursor.pointer(KObjectRefKind, "moPart_c")
    Require(cursor.read("<B"), (0,), "absent external unit component")
    words = cursor.read("<20I")
    Require(words[-1], KGeneration, "modern component reference generation")
    Require(
        tuple(words[index] for index in (6, 14, 15, 16, 17, 18)),
        (0,) * 6,
        "absent component extras",
    )
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


# callers supply the verified enclosing archive window so product scanning is unnecessary
def read_owned_face(blob, start, end, next_index, classes, objects):
    Require(0 <= start < end <= len(blob), True, "bounded face plane window")
    Require(
        classes.keys().isdisjoint(objects),
        True,
        "distinct archive class and object indices",
    )
    cursor = FaceCursor(blob[:end], start, next_index, dict(classes), dict(objects))
    index = cursor.pointer(KDefinitionKind, "moFaceRefPlnData_c")
    plane = read_plane_data(cursor)
    component = read_component_face(cursor)
    close_plane_data(cursor, plane)
    Require(cursor.read("<i"), (0,), "face-based component plane axis code")
    Require(cursor.position, end, "exact enclosing support return")
    return {
        "plane_data_object": index,
        "support_end": end,
        "next_map_index": cursor.next_index,
        "plane": plane,
        "component": component,
    }
