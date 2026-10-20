"""Observed Pipe controls and single line/circle sketch-path references."""

import math
import struct

from decode_selection import resolve_single_sketch_curve
from decode_sketch import reference


def decode_pipe(data, records, body, feature, features, *, path_resolver=None):
    if (feature["class_guid"] != "73615646-8752-4EE6-AD02-0B90804B7CD7"
            or body[:6] != bytes.fromhex("000100000000") or body[6] not in (0, 1)
            or struct.unpack_from("<I", body, 7)[0] != 4 or body[11:13] != b"\0\1" or body[68] != 0):
        raise ValueError("Unsupported observed Pipe prefix/operation")

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
    path = (path_resolver(data, records, path_id, feature["object_id"], features) if path_resolver
            else resolve_single_sketch_curve(data, records, path_id, feature["object_id"], features, ("Line", "Circle")))
    closed = path["is_closed"]
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
            "path": path,
            "fraction_scope": "Observed API mapping for this prefix and single sketch line/circle; native role names retained",
            "thickness_scope": "Stored thickness retained for solid pipes; exposed API parameter can exist even when hollow mode is false",
            "input_selection_status": "Single sketch curve resolved by explicit sketch ID/tag; composite/edge/proxy occurrence paths unsupported"}
