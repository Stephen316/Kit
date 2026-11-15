"""Walk the guarded P04 support component to its owned face plane data."""

from convert.adapters.solidworks.container.Archive import KClassRefKind, ReadString
from FaceOccurrence import read_face_data, read_local_component
from SketchRoot import Require


# empty labels keep the replay on the witnessed ordinary feature layout
def read_empty_label(cursor):
    name, width = ReadString(cursor.blob, cursor.position)
    Require(name, "", "empty feature label")
    cursor.position += width


# the embedded plane concept has neither its own node name nor resolved child entries
def read_plane_concept(cursor):
    cursor.null()  # moNodeName_c
    Require(cursor.read("<iIii"), (0, 0x40000000, -1, 0), "embedded plane node")
    read_empty_label(cursor)
    Require(cursor.read("<i"), (0,), "absent lightweight child list")
    cursor.null()  # moVisualProperties_c
    Require(cursor.read("<Hi"), (0, 0), "empty resolved node list")


# both embedded planes and named nodes need the same modern feature base framing
def read_feature_base(cursor):
    mode, _, _ = cursor.read("<2iI")
    Require(mode, 0, "ordinary feature mode")
    Require(cursor.read("<B"), (0,), "absent alternate feature label")
    cursor.read("<4i")
    cursor.vector(1)
    cursor.read("<i")
    cursor.null()  # moFolder_c
    read_empty_label(cursor)
    Require(cursor.read("<B"), (0,), "observed editable state")
    cursor.read("<HHBIHhf")  # entity display, style and line width
    cursor.read("<2i")
    cursor.null()  # moFeatComment_c
    cursor.read("<IBB")
    cursor.read("<5iH2i")  # includes the modern feature field at sldmodu+0x9d1bc4


# the local atom branch owns the temporary surface arrays and rollback state
def read_plane_atom(cursor):
    Require(cursor.read("<3H"), (0, 0, 0), "empty source atom lists and keeper")
    Require(cursor.read("<2i"), (0, 0), "absent transfer arrays")
    cursor.null()  # moAtom_c
    count, mode = cursor.read("<2i")
    Require(count, 0, "empty atom id list")
    Require(mode in range(4), True, "known atom body mode")
    arrays_offset = cursor.position

    Require(cursor.read("<i"), (0,), "absent profile atom array")
    cursor.read("<i")
    chooser, flags, other_chooser = cursor.read("<3H")
    Require((chooser, other_chooser), (0, 0), "absent base body choosers")
    cursor.read("<i")
    Require(cursor.read("<2H"), (0, 0), "absent additional body choosers")
    cursor.read("<i")
    Require(cursor.read("<i"), (0,), "absent action array")

    Require(cursor.read("<i"), (1,), "saved local partition record")
    cursor.null()  # moPMarkRecord_c
    Require(cursor.read("<3i"), (0, 0, 0), "empty local partition fields")
    cursor.read("<i")
    Require(cursor.read("<3i"), (0, 0, 0), "empty atom maps")
    cursor.read("<i")
    Require(
        cursor.read("<4i"),
        (0, 0, 0, 0),
        "absent visual map animation and face labels",
    )
    cursor.read("<i")
    return arrays_offset, flags


# the reference point and type precede the owned plane data pointer on this branch
def read_ref_geometry(cursor):
    point = cursor.vector(3)
    mode, _ = cursor.read("<2i")
    Require(mode, 4, "component-owned plane geometry mode")
    cursor.null()  # moFeatureRefWrapper_c
    Require(cursor.read("<i"), (0,), "guarded plane geometry trailer")
    return point


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
