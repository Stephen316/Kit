"""Observed Pipe controls and single line/circle sketch-path references."""

import math
import struct

from decode_selection import native_proxy_references
from decode_sketch import reference


def decode_pipe(data, records, body, feature, features):
    if (feature["class_guid"] != "73615646-8752-4EE6-AD02-0B90804B7CD7"
            or body[:6] != bytes.fromhex("000100000000") or body[6] not in (0, 1)
            or struct.unpack_from("<I", body, 7)[0] != 4 or body[11:13] != b"\0\1" or body[68] != 0):
        raise ValueError("Unsupported observed Pipe prefix/operation")

    def primary(identity, guid):
        choices = [r for r in records if r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(choices) != 1:
            raise ValueError("Pipe typed reference missing or ambiguous")
        return choices[0]

    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}

    def parameter(offset, role):
        identity = reference(body, offset)
        parameter = bindings.get(identity)
        if parameter is None or parameter["role"] != role:
            raise ValueError("Pipe binding role disagrees with field: "+role)
        return parameter["raw_float64"], identity

    against, against_binding = parameter(13, "AgainstDistance")
    along, along_binding = parameter(24, "AlongDistance")
    size, size_binding = parameter(46, "SectionSize")
    thickness, thickness_binding = parameter(57, "SectionThickness")
    section = struct.unpack_from("<I", body, 80)[0]
    if section not in (0, 1, 2) or not (0 < against <= 1 and 0 < along <= 1 and size > 0 and thickness >= 0):
        raise ValueError("Unsupported Pipe section or parameter range")
    path_id = reference(body, 69)
    proxy = primary(path_id, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
    chunk = data[proxy.body:proxy.end]
    if reference(chunk, len(chunk)-11) != feature["object_id"]:
        raise ValueError("Pipe path owner disagrees with feature")
    descriptors, _ = native_proxy_references(data, proxy)
    if len(descriptors) != 1:
        raise ValueError("Only observed single-curve Pipe paths supported")
    descriptor = primary(descriptors[0], "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
    chunk = data[descriptor.body:descriptor.end]
    if len(chunk) != 263 or chunk[:2] != b"\0\0" or reference(chunk, 252) != feature["object_id"]:
        raise ValueError("Unsupported Pipe path descriptor layout/owner")
    terminal_id = reference(chunk, 2)
    terminal = primary(terminal_id, "E2CEFD18-D755-4E09-8E7F-953A2F6D43F8")
    chunk = data[terminal.body:terminal.end]
    if len(chunk) != 26 or chunk[:10] != b"\0"*10:
        raise ValueError("Unsupported Pipe sketch-curve leaf")
    sketch_id, tag = struct.unpack_from("<QQ", chunk, 10)
    sketches = [f for f in features if f["kind"] == "Sketch" and f["sketch_object_id"] == sketch_id]
    curves = [g for f in sketches for g in f.get("geometry", []) if g.get("entity_tag") == tag and g["kind"] in ("Line", "Circle")]
    if len(curves) != 1:
        raise ValueError("Pipe path sketch/curve tag missing or ambiguous")
    curve = curves[0]
    closed = curve["kind"] == "Circle"
    if not closed and not math.isclose(along, against, abs_tol=1e-12):
        raise ValueError("Observed open Pipe fraction copies disagree")
    if closed and against+along > 1.+1e-12:
        raise ValueError("Closed Pipe fractions exceed the observed domain")
    return {"operation": "NewBody", "is_hollow": bool(body[6]), "section_type": {0: "Circular", 1: "Square", 2: "Triangular"}[section],
            "stored_section_type_code": section, "section_size_cm": size,
            "active_section_thickness_cm": thickness if body[6] else None,
            "stored_section_thickness_cm": thickness, "distance_one_fraction": against,
            "distance_two_fraction": along if closed else None, "native_against_fraction": against,
            "native_along_fraction": along,
            "parameter_bindings": {"AgainstDistance": against_binding, "AlongDistance": along_binding,
                                   "SectionSize": size_binding, "SectionThickness": thickness_binding},
            "path": {"selection_record_object_id": path_id, "descriptor_object_id": descriptors[0],
                     "terminal_object_id": terminal_id, "sketch_object_id": sketch_id,
                     "curve_object_id": curve["object_id"], "curve_entity_tag": tag, "kind": curve["kind"], "is_closed": closed},
            "fraction_scope": "Observed API mapping for this prefix and single sketch line/circle; native role names retained",
            "thickness_scope": "Stored thickness retained for solid pipes; exposed API parameter can exist even when hollow mode is false",
            "input_selection_status": "Single sketch curve resolved by explicit sketch ID/tag; composite/edge/proxy occurrence paths unsupported"}
