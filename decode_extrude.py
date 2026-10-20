"""Observed variable-length extrusion references and start/end condition fields."""

import math
import struct

from decode_sketch import numbers, reference


def optional_reference(body, cursor):
    if body[cursor] == 0:
        return None, cursor+1
    return reference(body, cursor), cursor+11


def decode_extrude(body, feature):
    if body[:6] != b"\0\x01\0\0\0\0":
        raise ValueError("Unsupported extrusion prefix")
    source, cursor = optional_reference(body, 6)
    if body[cursor:cursor+2] != b"\0\0":
        raise ValueError("Unsupported extrusion source separator")
    cursor += 2
    operation, mode = struct.unpack_from("<II", body, cursor)
    operation_kind = {1: "Join", 2: "Cut", 3: "Intersect", 4: "NewBody"}.get(operation, "Unknown")
    mode_kind = {1: "OneSided", 2: "TwoSided", 3: "Symmetric"}.get(mode, "Unknown")
    if body[cursor+12:cursor+14] != b"\0\x01":
        raise ValueError("Unsupported extrusion start prefix")
    start_code = struct.unpack_from("<I", body, cursor+14)[0]
    start_kind = {0: "ProfilePlane", 1: "Offset", 2: "FromEntity"}.get(start_code, "Unknown")
    direction = numbers(body, cursor+18, 3)
    if not math.isclose(sum(v*v for v in direction), 1., abs_tol=1e-9):
        raise ValueError("Unsupported extrusion direction vector")
    cursor += 42
    refs = {}
    for label in ("start", "against", "along", "opaque", "second_descriptor", "taper", "target"):
        refs[label], cursor = optional_reference(body, cursor)
    code_one = struct.unpack_from("<I", body, cursor)[0]
    cursor += 4
    refs["offset"], cursor = optional_reference(body, cursor)
    flags_one, enabled_two, code_two = struct.unpack_from("<III", body, cursor)
    cursor += 12
    refs["target_two"], cursor = optional_reference(body, cursor)
    if body[cursor] != 0:
        raise ValueError("Unsupported second-extent separator")
    flags_two = struct.unpack_from("<I", body, cursor+1)[0]
    cursor += 5
    for label in ("taper_two", "offset_two"):
        refs[label], cursor = optional_reference(body, cursor)
    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}

    def value(label, role, required=False):
        identity = refs[label]
        if identity is None and not required:
            return None
        parameter = bindings.get(identity)
        if parameter is None or parameter["role"] != role:
            raise ValueError("Extrusion parameter reference does not resolve: "+label)
        return parameter["raw_float64"]

    start = {"stored_code": start_code, "kind": start_kind}
    if start_code in (1, 2):
        start["offset_cm"] = value("start", "ProfileOffset", True)
    if start_code == 2:
        if source is None:
            raise ValueError("Missing entity start selection record")
        start["selection_record_object_id"] = source
        start["selection_status"] = "Entity selection unresolved"

    def side(code, distance_label, distance_role, taper_label, taper_role, offset_label, offset_role, target, flags):
        condition = {1: "Distance", 2: "ToEntity", 4: "ThroughAll"}.get(code, "Unknown")
        result = {"stored_code": code, "condition": condition, "uninterpreted_flags": flags}
        taper = value(taper_label, taper_role)
        if taper is not None:
            result.update(taper_angle_radians=taper, taper_angle_degrees=math.degrees(taper))
        if code == 1:
            result["distance_cm"] = value(distance_label, distance_role, True)
        elif code == 2:
            result["offset_cm"] = value(offset_label, offset_role, True)
            result["selection_status"] = "Target geometry selection unresolved"
        if target is not None:
            result["selection_record_object_id"] = target
        return result

    one = side(code_one, "along", "AlongDistance", "taper", "TaperAngle", "offset", "Side1Offset", refs["target"], flags_one)
    extent = {"stored_code": mode, "mode": mode_kind, "side_one": one,
              "side_one_condition": one["condition"], "stored_direction_vector": direction,
              "direction_scope": "Stored vector; distance sign also affects extrusion direction"}
    if "distance_cm" in one:
        extent["side_one_distance_cm"] = [one["distance_cm"]]
    if mode == 2:
        two = side(code_two, "against", "AgainstDistance", "taper_two", "Side2TaperAngle",
                   "offset_two", "Side2Offset", refs["target_two"], flags_two)
        extent["side_two"] = two
        if "distance_cm" in two:
            extent["side_two_distance_cm"] = [two["distance_cm"]]
    if mode == 3:
        convention = struct.unpack_from("<I", body, cursor)[0]
        extent.update(stored_distance_convention=convention,
                      distance_convention={1: "FullLength", 2: "HalfLength"}.get(convention, "Unknown"))
    unresolved = []
    if operation_kind == "Unknown" or mode_kind == "Unknown" or start_kind == "Unknown":
        unresolved.append("Unrecognized operation, extent mode or start condition")
    if one["condition"] == "Unknown" or (mode == 2 and extent["side_two"]["condition"] == "Unknown"):
        unresolved.append("Unrecognized end condition")
    if source or code_one == 2 or (mode == 2 and code_two == 2):
        unresolved.append("Referenced start/end geometry selection not decoded")
    return {"operation": {"stored_code": operation, "kind": operation_kind}, "extent": extent,
            "start": start, "extrusion_reference_fields": refs,
            "stored_second_extent_enabled": enabled_two}, unresolved
