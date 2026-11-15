"""Read the shared modern resolved list through its principal planes and origin."""

from struct import unpack_from


# the annotations cabinet and ordinary named features share lightweight concept framing
def read_named_concept(cursor, expected_flags):
    from convert.adapters.solidworks.container.Archive import ReadString
    from SketchRoot import Require
    from SupportPlane import read_empty_label

    name, length = ReadString(cursor.blob, cursor.position)
    cursor.position += length
    node_state, flags, node_id, node_tail = cursor.read("<iIii")
    Require((node_state, node_tail), (0, 0), "ordinary typed node")
    Require(flags in expected_flags, True, "witnessed typed node flags")
    read_empty_label(cursor)
    Require(cursor.read("<i"), (0,), "empty lightweight child list")
    cursor.null()  # moVisualProperties_c
    return name, node_id


# ordinary features can proceed to their own fields after an empty resolved list
def read_named_feature(cursor, expected_flags=(0x40000000,)):
    from SketchRoot import Require
    from SupportPlane import read_feature_base

    name, node_id = read_named_concept(cursor, expected_flags)
    Require(cursor.read("<Hi"), (0, 0), "empty resolved node list and tail")
    read_feature_base(cursor)
    return name, node_id


# folder subclasses share a named feature base and keep their own guarded suffixes
def read_folder(cursor, type_name, suffix_format, suffix, null_children=0):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
    )
    from SketchRoot import Require

    offset = cursor.position
    object_index = cursor.pointer(KDefinitionKind, type_name)
    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, feature_id = read_named_feature(cursor)
    Require(cursor.read(suffix_format), suffix, f"guarded {type_name} suffix")
    for _ in range(null_children):
        cursor.null()
    return {
        "class": type_name,
        "name": name,
        "native_feature_id": feature_id,
        "object_index": object_index,
        "offset": offset,
        "cursor": cursor.position,
        "next_map_index": cursor.next_index,
    }


# the notes start and end tag use the same inherited folder framing
def read_notes_base(cursor):
    from convert.adapters.solidworks.container.Archive import KClassRefKind
    from SketchRoot import Require

    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, native_id = read_named_feature(cursor)
    Require(cursor.read("<2i"), (1, 0), "guarded notes folder base")
    return {"name": name, "native_feature_id": native_id}


# cabinet membership includes a backreference to the already allocated end tag
def read_detail_cabinet(cursor):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
        KObjectRefKind,
    )
    from SketchRoot import Require
    from SupportPlane import read_feature_base

    offset = cursor.position
    cabinet = cursor.pointer(KDefinitionKind, "moDetailCabinet_c")
    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, native_id = read_named_concept(cursor, (0x40000000,))
    Require(cursor.read("<H"), (2,), "two resolved cabinet members")

    notes_class = "moNotesAreaFtrFolder_c"
    notes = cursor.pointer(KDefinitionKind, notes_class)
    notes_fields = read_notes_base(cursor)
    end_tag = cursor.pointer(KClassRefKind, notes_class)
    end_fields = read_notes_base(cursor)
    Require(
        cursor.pointer(KObjectRefKind, notes_class),
        notes,
        "end tag points to notes owner",
    )
    Require(cursor.read("<4i"), (0, 0, 1, 1), "guarded end tag trailer")
    Require(cursor.read("<4i"), (1, 0, 1, 1), "guarded notes trailer")

    Require(
        cursor.pointer(KObjectRefKind, notes_class),
        end_tag,
        "second cabinet member is the same end tag",
    )
    Require(cursor.read("<i"), (0,), "guarded cabinet list trailer")
    read_feature_base(cursor)
    tail = bytes(12) + b"\xf0\x3f" + bytes(6) + b"\xf0\x3f" + bytes(10)
    Require(cursor.read("<32s"), (tail,), "guarded cabinet scalar tail")
    return {
        "class": "moDetailCabinet_c",
        "name": name,
        "native_feature_id": native_id,
        "object_index": cabinet,
        "offset": offset,
        "cursor": cursor.position,
        "next_map_index": cursor.next_index,
        "notes": {**notes_fields, "object_index": notes},
        "end_tag": {**end_fields, "object_index": end_tag},
    }


# the principal plane payload owns the stored world normal and display frame
def read_default_plane_data(cursor, pointer_kind):
    from convert.adapters.solidworks.resolved.PlaneGeom import ReadDatumData

    datum = ReadDatumData(cursor, pointer_kind)
    return {
        "object_index": datum.ObjectIndex,
        "point_metres": datum.PointMetres,
        "normal_world": datum.NormalWorld,
        "transform": {
            "basis": datum.BasisValue,
            "translation_scale": datum.ShiftScale,
        },
    }


# principal planes use the same model feature and atom as component reference planes
def read_principal_plane(cursor, pointer_kind):
    from convert.adapters.solidworks.container.Archive import KClassRefKind
    from SketchRoot import Require
    from SupportPlane import read_plane_atom, read_ref_geometry

    offset = cursor.position
    plane = cursor.pointer(pointer_kind, "moRefPlane_c")
    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, feature_id = read_named_feature(cursor, expected_flags=(0xC0000000,))
    Require(cursor.read("<i"), (0,), "guarded principal model feature")
    read_plane_atom(cursor)
    read_ref_geometry(cursor, expected_mode=5)
    data = read_default_plane_data(cursor, pointer_kind)
    return {
        "name": name,
        "native_feature_id": feature_id,
        "offset": offset,
        "cursor": cursor.position,
        "object_index": plane,
        "next_map_index": cursor.next_index,
        "plane_data": data,
    }


# origin and user profiles both need the same framing for the earlier null pointer
def read_profile_body_prefix(cursor, expected_flags):
    from SketchRoot import Require

    name, feature_id = read_named_feature(cursor, expected_flags)
    cursor.read("<i")  # moModelFeature_c
    Require(cursor.read("<i"), (0,), "guarded scalar before the early profile pointer")
    early_pointer = cursor.position
    cursor.null()
    Require(cursor.read("<i"), (0,), "guarded scalar after the early profile pointer")
    return name, feature_id, early_pointer


# the origin materializes a resolved only sketch through the retained configuration class
def read_origin_entry(cursor):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
    )
    from OriginTail import read_feature_tail, read_presentation
    from SketchRoot import Require

    offset = cursor.position
    origin = cursor.pointer(KDefinitionKind, "moOriginProfileFeature_c")
    cursor.pointer(KClassRefKind, "moNodeName_c")
    name, feature_id, _ = read_profile_body_prefix(cursor, (0xC0000000,))
    Require((name, feature_id), ("Origin", 5), "typed origin profile")
    sketch_offset = cursor.position
    sketch_kind = (
        KClassRefKind if "sgSketch" in cursor.classes.values() else KDefinitionKind
    )
    sketch = cursor.pointer(sketch_kind, "sgSketch")
    geometry = read_origin_geometry(cursor, sketch_offset, sketch)
    presentation = read_presentation(cursor)
    tail = read_feature_tail(cursor)
    return {
        "name": name,
        "native_feature_id": feature_id,
        "offset": offset,
        "object_index": origin,
        "sketch_offset": sketch_offset,
        "sketch_object": sketch,
        "geometry": geometry,
        "presentation": presentation,
        **tail,
        "end": cursor.position,
        "next_map_index": cursor.next_index,
    }


# the origin relation refers to a point handle within the sole origin point
def read_origin_geometry(cursor, sketch_offset, sketch_object):
    from SketchCursor import SketchCursor
    from SketchGeom import ReadDims, ReadPointItem
    from SketchRoot import Require

    sketch = SketchCursor.FromEnclosing(cursor, sketch_offset, sketch_object)
    body = sketch.Offset
    Require(sketch.ReadCount(), 1, "one origin point")
    _, _, point = ReadPointItem(sketch)
    Require(point, (0, 0), "origin point coordinates")
    Require(sketch.ReadCount(), 0, "empty origin lines")
    ReadDims(sketch)
    Require(sketch.Dimensions, [], "empty origin value dimensions")
    Require(sketch.ReadValue("<3H"), (0, 0, 1), "one origin member relation")
    _, _, type_code = sketch.ReadDimBase(None)
    Require(type_code, 17, "witnessed origin relation type")
    Require(sketch.ReadValue("<2H"), (65534, 0), "guarded origin relation fields")
    handle = sketch.ReadObject("sgPointHandle")
    Require(
        sketch.Handles[handle], (0, -1, 0), "relation targets the local origin point"
    )
    cursor.position = sketch.Offset
    cursor.next_index = sketch.NextIndex
    return {
        "body": body,
        "end": cursor.position,
        "point_metres": point,
        "point_relation_type": type_code,
        "point_handle_object": handle,
    }


# folder suffixes are confined to the ordinary bodies at the start of these captures
def read_resolved_prelude(blob, config_map, expected_count):
    from convert.adapters.solidworks.container.Archive import (
        KClassRefKind,
        KDefinitionKind,
        KObjectRefKind,
    )
    from FaceOccurrence import FaceCursor
    from SketchRoot import Require

    base, count = unpack_from("<iH", blob)
    Require(base, config_map.NextIndex, "derived configuration map counter")
    Require(count, expected_count, "witnessed short resolved list")
    cursor = FaceCursor(
        blob,
        6,
        config_map.NextIndex,
        config_map.Classes.copy(),
        config_map.Objects.copy(),
    )
    folders = [
        read_folder(cursor, "moCommentsFolder_c", "<2i", (0, 0)),
        read_folder(cursor, "moFavoriteFolder_c", "<4i", (1, 0, 0, 1)),
        read_folder(cursor, "moHistoryFolder_c", "<2iH", (1, 0, 0)),
        read_folder(
            cursor,
            "moSelectionSetFolder_c",
            "<2i6s",
            (1, 0, b"\x00\x00\x01\x00\x00\x00"),
        ),
        read_folder(cursor, "moSensorFolder_c", "<2i", (1, 0)),
        read_folder(cursor, "moDocsFolder_c", "<2i", (1, 0)),
        read_detail_cabinet(cursor),
        read_folder(
            cursor, "moSurfaceBodyFolder_c", "<4i", (1, 0, 0, 0), null_children=2
        ),
        read_folder(
            cursor, "moSolidBodyFolder_c", "<4i", (1, 0, 0, 0), null_children=2
        ),
    ]
    alias_start = cursor.position
    environment = cursor.pointer(KObjectRefKind, "moEnvFolder_c")
    folders.extend(
        [
            read_folder(cursor, "moInkMarkupFolder_c", "<2i", (1, 0)),
            read_folder(cursor, "moEqnFolder_c", "<2i", (1, 0)),
            read_folder(
                cursor,
                "moMaterialFolder_c",
                "<2i8s",
                (1, 0, b"\xff\xfe\xff\x00\x00\x00\x00\x80"),
            ),
        ]
    )
    planes = [read_principal_plane(cursor, KDefinitionKind)]
    planes.extend(read_principal_plane(cursor, KClassRefKind) for _ in range(2))
    Require(
        [
            (
                item["name"],
                item["native_feature_id"],
                item["plane_data"]["normal_world"],
            )
            for item in planes
        ],
        [
            ("Front Plane", 2, (0, 0, 1)),
            ("Top Plane", 3, (0, 1, 0)),
            ("Right Plane", 4, (1, 0, 0)),
        ],
        "guarded principal plane identities and orientation",
    )
    origin = read_origin_entry(cursor)
    front, *_ = planes
    Require(
        origin["support"]["native_feature_id"],
        front["native_feature_id"],
        "origin support resolves the saved front plane",
    )
    origin["support"]["plane_object"] = front["object_index"]
    return cursor, {
        "list_count": count,
        "prior_map_index": base,
        "folders": folders,
        "environment_alias": {"offset": alias_start, "object_index": environment},
        "principal_planes": planes,
        "origin": origin,
    }
