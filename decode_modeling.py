"""Limited modeling-feature fields inferred from controlled Fusion exports."""

import math
import struct

from decode_extrude import decode_extrude


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
            if not body.startswith(b"\0\x01"):
                raise ValueError("Unrecognized modeling-feature prefix")
            roles = {}
            for parameter in feature["parameters"]:
                roles.setdefault(parameter["role"], []).append(parameter)
            feature["parameter_roles"] = roles
            if feature["kind"] == "Extrude":
                fields, reasons = decode_extrude(body, feature)
                feature.update(fields)
                unknown.extend({"object_id": feature["object_id"], "reason": reason} for reason in reasons)
            else:
                operation = struct.unpack_from("<I", body, 6)[0]
                # Only the new-body revolve operation has reference evidence.
                feature["operation"] = {"stored_code": operation, "kind": "NewBody" if operation == 4 else "Unknown"}
                feature["revolve"] = {"axis_selection": "Undecoded"}
                if "AlongAngle" in roles and len(roles["AlongAngle"]) == 1:
                    angle = roles["AlongAngle"][0]["raw_float64"]
                    feature["revolve"].update(angle_radians=angle, angle_degrees=math.degrees(angle),
                                               is_full_turn=math.isclose(abs(angle), 2*math.pi, abs_tol=1e-10))
        except (ValueError, IndexError, struct.error) as error:
            unknown.append({"object_id": feature["object_id"], "reason": str(error)})
    return {"unresolved": unknown, "scope": "Observed extrusion starts/end conditions and revolve angles; no body regeneration"}
