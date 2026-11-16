"""Read the shared modern resolved list through its principal planes and origin."""

from convert.adapters.solidworks.Resolved.NamedNode import ReadNamedNode as read_named_concept
from convert.adapters.solidworks.Resolved.OriginProfile import ReadOrigin
from convert.adapters.solidworks.Resolved.ProfileEntry import ReadProfileHead as read_profile_body_prefix
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved


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


# origin reports retain every field through the typed feature return
def report_origin(origin):
    geometry = origin.Geometry
    return {
        "name": origin.NameValue,
        "native_feature_id": origin.FeatureId,
        "offset": origin.Offset,
        "object_index": origin.ObjectIndex,
        "sketch_offset": origin.SketchOffset,
        "sketch_object": origin.SketchIndex,
        "geometry": {
            "body": geometry.Offset,
            "end": geometry.EndOffset,
            "point_metres": geometry.PointValue,
            "point_relation_type": geometry.RelationType,
            "point_handle_object": geometry.Handle,
        },
        "presentation": {
            "lists": [
                {"offset": item.Offset, "object_index": item.ObjectIndex, "end": item.EndOffset}
                for item in origin.Lists
            ],
            "sketch_end": origin.DisplayEnd,
        },
        "support": {
            "offset": origin.Support.Offset,
            "object_index": origin.Support.ObjectIndex,
            "unit_component": origin.Support.UnitIndex,
            "part_object": origin.Support.PartIndex,
            "native_feature_id": origin.Support.FeatureId,
            "native_time_word": origin.Support.TimeValue,
        },
        "feature_state_word": origin.StateValue,
        "end": origin.EndOffset,
        "next_map_index": origin.NextIndex,
    }


# folder suffixes are confined to the ordinary bodies at the start of these captures
def read_resolved_prelude(blob, config_map, expected_count):
    from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix
    from FaceOccurrence import FaceCursor
    from SketchRoot import KGeneration, Require

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
    origin = report_origin(ReadOrigin(cursor, KGeneration))
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
