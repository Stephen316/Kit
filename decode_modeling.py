"""Limited modeling-feature fields inferred from controlled Fusion exports."""

import struct

from decode_extrude import decode_extrude
from decode_revolve import decode_revolve


def decode_modeling(data, records, features):
    by_offset = {r.start: r for r in records}
    unknown = []
    for feature in features:
        if feature["kind"] not in ("Extrude", "Revolve"):
            if feature["kind"] not in ("Sketch", "UnsupportedFeature"):
                feature["decode_level"] = "Named feature and observed numeric parameters only"
                feature["unresolved_inputs"] = ["Geometry/topology selection and feature-specific settings"]
            continue
        record = by_offset[feature["record_offset"]]
        body = data[record.body:record.end]
        try:
            roles = {}
            for parameter in feature["parameters"]:
                roles.setdefault(parameter["role"], []).append(parameter)
            feature["parameter_roles"] = roles
            if feature["kind"] == "Extrude":
                fields, reasons = decode_extrude(body, feature)
                feature.update(fields)
                unknown.extend({"object_id": feature["object_id"], "reason": reason} for reason in reasons)
            else:
                feature.update(decode_revolve(body, feature))
        except (ValueError, IndexError, struct.error) as error:
            unknown.append({"object_id": feature["object_id"], "reason": str(error)})
    return {"unresolved": unknown, "scope": "Observed extrusion starts/ends and angular revolve modes; no body regeneration"}
