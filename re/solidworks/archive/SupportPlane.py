"""Walk the guarded P04 support component to its owned face plane data."""

from convert.adapters.solidworks.container.Archive import KClassRefKind
from convert.adapters.solidworks.resolved.PlaneAtom import (
    ReadAtomMaps as read_partition_tail,
    ReadPlaneAtom as read_plane_atom,
)
from convert.adapters.solidworks.resolved.PlaneGeom import ReadRefGeom
from FaceOccurrence import read_face_data, read_local_component
from FeatureBase import read_empty_label, read_feature_base
from SketchRoot import Require


# the embedded plane concept has neither its own node name nor resolved child entries
def read_plane_concept(cursor):
    cursor.null()  # moNodeName_c
    Require(cursor.read("<iIii"), (0, 0x40000000, -1, 0), "embedded plane node")
    read_empty_label(cursor)
    Require(cursor.read("<i"), (0,), "absent lightweight child list")
    cursor.null()  # moVisualProperties_c
    Require(cursor.read("<Hi"), (0, 0), "empty resolved node list")


# both embedded and principal records use the packaged geometry framing
def read_ref_geometry(cursor, expected_mode=4):
    return ReadRefGeom(cursor, expected_mode)


# the component and its local plane must resolve before the nested face reader starts
def read_reference_plane(cursor, context):
    Require(context, 0, "witnessed support archive context")
    support = cursor.pointer(KClassRefKind, "moCompRefPlane_c")
    unit, part = read_local_component(cursor)
    feature_id, time_word = cursor.read("<iI")
    Require(feature_id, -1, "embedded plane carries its own geometry")
    plane_object = cursor.pointer(KClassRefKind, "moRefPlane_c")
    read_plane_concept(cursor)
    read_feature_base(cursor)
    cursor.read("<i")  # moModelFeature_c
    atom_start = cursor.position
    arrays_offset, atom_flags = read_plane_atom(cursor)
    atom_end = cursor.position
    point = read_ref_geometry(cursor)
    data_start = cursor.position
    face = read_face_data(cursor)
    return {
        "support_object": support,
        "unit_component": unit,
        "part_object": part,
        "native_time_word": time_word,
        "ref_plane_object": plane_object,
        "atom_span": (atom_start, atom_end),
        "atom_arrays_offset": arrays_offset,
        "atom_flags": atom_flags,
        "reference_point_metres": point,
        "plane_data_start": data_start,
        "face": face,
    }
