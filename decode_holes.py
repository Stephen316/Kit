"""Observed single-position, default-direction Fusion hole records."""

import math
import struct

from decode_extrude import optional_reference
from decode_sketch import attributes, numbers, reference, same


def decode_hole(data, records, body, feature):
    props, cursor = attributes(body, 2)
    head = body[cursor:]
    if body[:2] == b"\0\0" and head[:4] == bytes.fromhex("01010000"):
        extent, base = "Distance", 4
    elif body[:2] == b"\0\x01" and head[:8] == bytes.fromhex("0000000001010100"):
        extent, base = "ThroughAll", 8
    elif body[:2] == b"\0\x01" and head[:8] == bytes.fromhex("0000000001010000"):
        extent, base = "ToEntity", 8
    else:
        raise ValueError("Unsupported hole extent/direction prefix")
    if head[base:base+20] != b"\x01"+b"\0"*19 or head[base+24:base+33] != b"\0"*9:
        raise ValueError("Unsupported hole positioning header")
    kind_code = struct.unpack_from("<I", head, base+20)[0]
    kinds = {0: "Simple", 1: "Counterbore", 2: "Countersink"}
    if kind_code not in kinds:
        raise ValueError("Unsupported hole type")
    cursor, refs = base+33, {}
    for label in ("CBDepth", "CBDiameter", "CSAngle", "CSDiameter"):
        refs[label], cursor = optional_reference(head, cursor)
    if struct.unpack_from("<I", head, cursor)[0] != 1:
        raise ValueError("Only observed single-position holes are supported")
    cursor += 4
    for label in ("position", "axis", "HoleDepth", "HoleDiameter", "opaque_core_input"):
        refs[label], cursor = optional_reference(head, cursor)
    if head[cursor:cursor+6] != b"\0"*6:
        raise ValueError("Unsupported hole tip separator")
    refs["TipAngle"] = reference(head, cursor+6)
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
                "tip_angle_radians": value("TipAngle", True), "is_default_direction": True,
                "extent": {"condition": extent}, "input_record_object_ids": refs,
                "thread_status": "Thread definitions unresolved; diameter is the stored model parameter",
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

    def geometry(label, guid, length, position_offset):
        choices = []
        for record in records:
            if record.object_id != refs[label] or record.class_guid != guid:
                continue
            chunk = data[record.body:record.end]
            if len(chunk) != length or reference(chunk, length-11) != feature["object_id"]:
                continue
            choices.append((numbers(chunk, position_offset, 3), chunk))
        if len(choices) != 1:
            raise ValueError("Hole geometry reference unresolved: "+label)
        return choices[0]

    position, _ = geometry("position", "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44", 178, 23)
    axis_position, axis = geometry("axis", "F2A7590D-6654-4674-B393-A2AEF4FEC48A", 202, 6)
    normal = numbers(axis, 30, 3)
    if axis[:6] != bytes.fromhex("000008000000") or not same(position, axis_position):
        raise ValueError("Hole position/axis disagree")
    if not math.isclose(sum(v*v for v in normal), 1., abs_tol=1e-9):
        raise ValueError("Hole supporting normal is not unit length")
    settings.update(position_cm=position, direction=[-v for v in normal],
                    coordinate_scope="Observed parent-component coordinates; assembly context unverified",
                    has_flat_tip=math.isclose(settings["tip_angle_radians"], math.pi, abs_tol=1e-9))
    return settings
