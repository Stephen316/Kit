"""Observed hole types, point placements, direction flags and extents."""

import math
import struct

from decode_extrude import optional_reference
from decode_sketch import attributes, numbers, reference, same


def decode_hole(data, records, body, feature):
    if body[:2] == b"\0\0":
        props, cursor = {}, 2
    elif body[:2] == b"\0\1":
        props, cursor = attributes(body, 2)
    else:
        raise ValueError("Unsupported hole attribute prefix")
    tap_type = struct.unpack_from("<I", body, cursor)[0]
    if tap_type not in (0, 2):
        raise ValueError("Unsupported hole tap type")
    if not body[1]:
        cursor += 4
    head = body[cursor:]
    if body[:2] == b"\0\0" and head[:4] == bytes.fromhex("01010000"):
        extent, base = "Distance", 4
    elif body[:2] == b"\0\x01" and head[4:8] == bytes.fromhex("01010100"):
        extent, base = "ThroughAll", 8
    elif body[:2] == b"\0\x01" and head[4:8] == bytes.fromhex("01010000"):
        extent, base = "ToEntity", 8
    else:
        raise ValueError("Unsupported hole extent/direction prefix")
    if head[base:base+20] != b"\x01"+b"\0"*19 or head[base+24] not in (0, 1):
        raise ValueError("Unsupported hole positioning header")
    kind_code = struct.unpack_from("<I", head, base+20)[0]
    kinds = {0: "Simple", 1: "Counterbore", 2: "Countersink"}
    if kind_code not in kinds:
        raise ValueError("Unsupported hole type")
    reversed_direction = bool(head[base+24])
    position_mode = struct.unpack_from("<I", head, base+25)[0]
    association_count = struct.unpack_from("<I", head, base+29)[0]
    if position_mode not in (0, 1) or not 0 <= association_count <= 1024:
        raise ValueError("Unsupported hole position mode or association count")
    associations = [{"record_object_id": reference(head, base+33+19*i),
                     "stored_point_tag": struct.unpack_from("<Q", head, base+44+19*i)[0]}
                    for i in range(association_count)]
    cursor, refs = base+33+19*association_count, {}
    for label in ("CBDepth", "CBDiameter", "CSAngle", "CSDiameter"):
        refs[label], cursor = optional_reference(head, cursor)
    count = struct.unpack_from("<I", head, cursor)[0]
    if not 1 <= count <= 1024 or (association_count and association_count != count):
        raise ValueError("Unsupported hole position count or association mismatch")
    cursor += 4
    positions = [reference(head, cursor+11*i) for i in range(count)]
    cursor += 11*count
    for label in ("axis", "HoleDepth", "HoleDiameter", "opaque_core_input", "center"):
        refs[label], cursor = optional_reference(head, cursor)
    if head[cursor:cursor+4] != b"\0"*4:
        raise ValueError("Unsupported hole tip separator")
    refs["thread"], cursor = optional_reference(head, cursor+4)
    refs["TipAngle"] = reference(head, cursor)
    if (refs["thread"] is not None) != (tap_type == 2):
        raise ValueError("Hole tap type and attached-thread reference disagree")
    if tap_type == 2:
        from decode_threads import thread_parent_hole
        threads = [r for r in records if r.is_primary and r.object_id == refs["thread"]
                   and r.class_guid == "584D9526-EF22-4F6F-9FE1-5FCF1F3CE575"]
        if len(threads) != 1 or thread_parent_hole(data[threads[0].body:threads[0].end]) != feature["object_id"]:
            raise ValueError("Hole/thread native references are not reciprocal")
    refs["positions"] = positions
    if count == 1:
        refs["position"] = positions[0]
    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}

    def value(role, required):
        identity = refs[role]
        if identity is None and not required:
            return None
        parameter = bindings.get(identity)
        if parameter is None or parameter["role"] != role:
            raise ValueError("Hole binding does not resolve: "+role)
        return parameter["raw_float64"]

    settings = {"hole_type": kinds[kind_code], "stored_hole_type": kind_code,
                "diameter_parameter_cm": value("HoleDiameter", True),
                "tip_angle_radians": value("TipAngle", True), "is_default_direction": not reversed_direction,
                "extent": {"condition": extent}, "input_record_object_ids": refs,
                "tap_type": {0: "Simple", 2: "Tapped"}[tap_type], "stored_tap_type_code": tap_type,
                "attached_thread_object_id": refs["thread"],
                "thread_status": ("Reciprocal attached thread reference decoded; definition is on the Thread feature"
                                  if tap_type == 2 else "No attached thread; diameter is the stored model parameter"),
                "support_selection_status": "Supporting face and topology unresolved"}
    depth = value("HoleDepth", extent == "Distance")
    if extent == "Distance":
        settings["extent"]["depth_cm"] = depth
    elif depth is not None:
        raise ValueError("Unexpected active depth in non-distance hole")
    if "SavedHoleDepthInNonDistanceExtentsCase" in props:
        settings["cached_inactive_depth_cm"] = props["SavedHoleDepthInNonDistanceExtentsCase"]
    if extent == "ToEntity":
        settings["extent"]["selection_status"] = "Target face unresolved"
    for role, output, enabled in (
            ("CBDepth", "counterbore_depth_cm", kind_code == 1),
            ("CBDiameter", "counterbore_diameter_cm", kind_code == 1),
            ("CSAngle", "countersink_angle_radians", kind_code == 2),
            ("CSDiameter", "countersink_diameter_cm", kind_code == 2)):
        result = value(role, enabled)
        if enabled:
            settings[output] = result
        elif result is not None:
            raise ValueError("Unexpected inactive hole-type binding: "+role)

    def geometry(identity, guid, length, position_offset):
        choices = []
        for record in records:
            if record.object_id != identity or record.class_guid != guid:
                continue
            chunk = data[record.body:record.end]
            if len(chunk) != length or reference(chunk, length-11) != feature["object_id"]:
                continue
            choices.append((numbers(chunk, position_offset, 3), chunk))
        if len(choices) != 1:
            raise ValueError("Hole geometry reference unresolved: "+str(identity))
        return choices[0]

    coordinates = [geometry(identity, "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44", 178, 23)[0] for identity in positions]
    axis_position, axis = geometry(refs["axis"], "F2A7590D-6654-4674-B393-A2AEF4FEC48A", 202, 6)
    normal = numbers(axis, 30, 3)
    if axis[:6] != bytes.fromhex("000008000000"):
        raise ValueError("Unsupported hole axis representation")
    if not math.isclose(sum(v*v for v in normal), 1., abs_tol=1e-9):
        raise ValueError("Hole supporting normal is not unit length")
    if position_mode == 1:
        if count != 1 or association_count or refs["center"] is None:
            raise ValueError("Unsupported center-edge hole placement combination")
        center, _ = geometry(refs["center"], "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44", 178, 23)
        if not same(center, coordinates[0]):
            raise ValueError("Hole edge-center position copies disagree")
        definition = "AtCenter"
    else:
        if refs["center"] is not None:
            raise ValueError("Unexpected hole center-edge descriptor")
        definition = ("SketchPoint" if count == 1 else "SketchPoints") if association_count else "Point"
    if count == 1:
        settings["position_cm"] = coordinates[0]
    settings.update(positions_cm=coordinates, position_count=count, position_definition=definition,
                    point_association_records=associations,
                    association_status="Stored placement references/tags retained; sketch-point and edge topology associations remain partial",
                    stored_axis_proxy_origin=axis_position,
                    direction=[v if reversed_direction else -v for v in normal],
                    coordinate_scope="Observed parent-component coordinates; assembly context unverified",
                    has_flat_tip=math.isclose(settings["tip_angle_radians"], math.pi, abs_tol=1e-9))
    return settings
