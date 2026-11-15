"""Read the shared modern resolved list through its principal planes and origin."""

from convert.adapters.solidworks.resolved.NamedNode import ReadNamedFeat
from convert.adapters.solidworks.resolved.NamedNode import ReadNamedNode as read_named_concept
from convert.adapters.solidworks.resolved.ResolvedHead import OpenResolved


# report the folder and its allocation without changing the reader's typed data
def report_folder(folder):
    return {
        "class": folder.ClassName,
        "name": folder.NameValue,
        "native_feature_id": folder.FeatureId,
        "object_index": folder.ObjectIndex,
        "offset": folder.Offset,
        "cursor": folder.EndOffset,
        "next_map_index": folder.NextIndex,
    }


def report_note(note):
    return {
        "name": note.NameValue,
        "native_feature_id": note.FeatureId,
        "object_index": note.ObjectIndex,
    }


def report_cabinet(details):
    return {
        **report_folder(details.Cabinet),
        "notes": report_note(details.Notes),
        "end_tag": report_note(details.EndTag),
    }


# the research report keeps the stored principal identity and all native spans
def report_principal(datum):
    geometry = datum.Geometry
    return {
        "name": datum.NameValue,
        "native_feature_id": datum.FeatureId,
        "offset": datum.Offset,
        "cursor": datum.EndOffset,
        "object_index": datum.ObjectIndex,
        "next_map_index": datum.NextIndex,
        "plane_data": {
            "object_index": geometry.ObjectIndex,
            "point_metres": geometry.PointMetres,
            "normal_world": geometry.NormalWorld,
            "transform": {
                "basis": geometry.BasisValue,
                "translation_scale": geometry.ShiftScale,
            },
        },
    }


# origin and user profiles both need the same framing for the earlier null pointer
def read_profile_body_prefix(cursor, expected_flags):
    from SketchRoot import Require

    name, feature_id = ReadNamedFeat(cursor, expected_flags)
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
    from convert.adapters.solidworks.resolved.SystemPrefix import ReadSysPrefix
    from FaceOccurrence import FaceCursor
    from SketchRoot import Require

    entry = OpenResolved(blob, config_map, expected_count)
    cursor = FaceCursor(
        entry.BlobValue,
        entry.Offset,
        entry.NextIndex,
        entry.Classes,
        entry.Objects,
    )
    system = ReadSysPrefix(cursor)
    folders = [report_folder(folder) for folder in system.FirstFolders]
    folders.append(report_cabinet(system.Details))
    folders.extend(report_folder(folder) for folder in system.LaterFolders)
    planes = [report_principal(plane) for plane in system.Planes]
    origin = read_origin_entry(cursor)
    front, *_ = planes
    Require(
        origin["support"]["native_feature_id"],
        front["native_feature_id"],
        "origin support resolves the saved front plane",
    )
    origin["support"]["plane_object"] = front["object_index"]
    return cursor, {
        "list_count": expected_count,
        "prior_map_index": config_map.NextIndex,
        "folders": folders,
        "environment_alias": {"offset": system.EnvOffset, "object_index": system.Environment},
        "principal_planes": planes,
        "origin": origin,
    }
