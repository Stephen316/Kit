"""Observed single-path, sketch-profile Sweep controls and explicit selections."""

import math
import struct

from decode_parameters import read_string
from decode_profiles import PROFILE_DESCRIPTOR_GUID, PROFILE_LOOP_GUID, read_loops
from decode_selection import native_proxy_references, resolve_single_sketch_curve
from decode_sketch import attributes, reference


SWEEP_GUID = "FCBB1707-4450-46B3-9E65-0F61682EA8CA"


def decode_sweep(data, records, body, feature, features):
    if (feature["class_guid"] != SWEEP_GUID or len(body) < 170
            or body[0] != 0 or body[1] not in (0, 1)):
        raise ValueError("Unsupported observed Sweep class/prefix")
    props, base = attributes(body, 2) if body[1] else ({}, 2)
    if props:
        raise ValueError("Unobserved Sweep attributes")
    if (body[base+4:base+11] != b"\x01"+struct.pack("<I", 3)+b"\0\0"
            or body[base+11] not in (0, 1)
            or body[base+12:base+38] != b"\x01\x01"+struct.pack("<ddd", 1., 0., 0.)
            or body[base+82] != 0 or body[base+94] != 0
            or struct.unpack_from("<I", body, base+132)[0] != 1):
        raise ValueError("Unsupported observed single-path Sweep control layout")
    orientation_code = struct.unpack_from("<I", body, base+128)[0]
    if orientation_code not in (1, 2):
        raise ValueError("Unobserved Sweep orientation")

    def primary(identity, guid):
        matches = [r for r in records if r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(matches) != 1:
            raise ValueError("Sweep typed reference missing or ambiguous")
        return matches[0]

    def owned(record):
        chunk = data[record.body:record.end]
        if reference(chunk, len(chunk)-11) != feature["object_id"]:
            raise ValueError("Sweep selection owner disagrees with feature")
        return chunk

    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}

    def parameter(offset, role):
        identity = reference(body, base+offset)
        binding = bindings.get(identity)
        if binding is None or binding["role"] != role:
            raise ValueError("Sweep binding role disagrees with field: "+role)
        value = binding["raw_float64"]
        if not math.isfinite(value):
            raise ValueError("Nonfinite Sweep parameter")
        return value, identity

    parameter_values, parameter_ids = {}, {}
    for offset, role in ((38, "AgainstDistance"), (49, "AgainstRailDistance"), (60, "AlongDistance"),
                         (71, "AlongRailDistance"), (106, "TaperAngle"), (117, "TwistAngle")):
        parameter_values[role], parameter_ids[role] = parameter(offset, role)
    if any(not 0 <= parameter_values[role] <= 1 for role in ("AgainstDistance", "AlongDistance")):
        raise ValueError("Sweep path fraction outside observed domain")

    if (parameter_values["AgainstDistance"] != 0
            or parameter_values["AgainstRailDistance"] != 1 or parameter_values["AlongRailDistance"] != 1):
        raise ValueError("Unobserved two-sided/guide Sweep distance layout")
    path_id = reference(body, base+83)
    path = resolve_single_sketch_curve(data, records, path_id, feature["object_id"], features, ("Line", "Arc"))
    profile_proxy_id = reference(body, base+136)
    proxy = primary(profile_proxy_id, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
    owned(proxy)
    descriptor_ids, _ = native_proxy_references(data, proxy)
    if len(descriptor_ids) != 1:
        raise ValueError("Only observed single-profile Sweep selections supported")
    descriptor = primary(descriptor_ids[0], PROFILE_DESCRIPTOR_GUID)
    chunk = owned(descriptor)
    if chunk[:2] != b"\0\0" or struct.unpack_from("<I", chunk, 13)[0] != 1:
        raise ValueError("Unsupported Sweep profile descriptor")
    namespace, cursor = read_string(chunk, 17)
    sketch_text, cursor = read_string(chunk, cursor)
    if len(namespace) != 36 or not sketch_text.isascii() or not sketch_text.isdecimal():
        raise ValueError("Unsupported Sweep explicit sketch identity")
    sketch_id = int(sketch_text)
    sketches = [f for f in features if f["kind"] == "Sketch" and f["sketch_object_id"] == sketch_id]
    if len(sketches) != 1:
        raise ValueError("Sweep profile sketch unresolved or ambiguous")
    definition_id = reference(chunk, 2)
    definition = primary(definition_id, PROFILE_LOOP_GUID)
    loops = read_loops(data[definition.body:definition.end], descriptor.object_id, sketches[0])
    profile = {"selection_record_object_id": profile_proxy_id, "descriptor_object_id": descriptor.object_id,
               "loop_definition_object_id": definition_id, "sketch_object_id": sketch_id,
               "sketch_name": sketches[0]["name"], "loops": loops,
               "scope": "Explicit sketch-curve membership and outer/inner loop flags; traversal and general trims unresolved"}
    code = struct.unpack_from("<I", body, base)[0]
    if code not in (2, 4):
        raise ValueError("Unsupported unverified Sweep operation")
    return {"operation": {2: "Cut", 4: "NewBody"}[code], "stored_operation_code": code,
            "orientation": {1: "Parallel", 2: "Perpendicular"}[orientation_code],
            "stored_orientation_code": orientation_code, "is_solid": bool(body[base+11]),
            "path_fraction": parameter_values["AlongDistance"],
            "stored_against_path_fraction": parameter_values["AgainstDistance"], "distance_two_fraction": None,
            "twist_angle_radians": parameter_values["TwistAngle"] if orientation_code == 2 else None,
            "stored_twist_angle_radians": parameter_values["TwistAngle"],
            "taper_angle_radians": parameter_values["TaperAngle"] if orientation_code == 2 else None,
            "stored_taper_angle_radians": parameter_values["TaperAngle"],
            "parameter_bindings": parameter_ids, "path": path, "profile": profile,
            "uninterpreted_control_header_hex": body[base+4:base+38].hex(),
            "stored_inactive_rail_fraction_values": {role: parameter_values[role] for role in ("AgainstRailDistance", "AlongRailDistance")},
            "guide_status": "No guide rail/surfaces in observed control prefix; guide variants unsupported",
            "input_selection_status": "Single sketch line/arc path and single sketch-profile membership resolved; general trims and composite/solid-body/guide paths unsupported"}
