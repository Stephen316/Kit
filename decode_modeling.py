"""Limited modeling-feature fields inferred from controlled Fusion exports."""

import math
import struct


def decode_modeling(data, records, features):
    by_offset = {r.start: r for r in records}
    unknown = []
    for feature in features:
        if feature["kind"] not in ("Extrude", "Revolve"):
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
                operation = struct.unpack_from("<I", body, 9)[0]
                operation_name = {1: "Join", 2: "Cut", 3: "Intersect", 4: "NewBody"}.get(operation)
                mode = struct.unpack_from("<I", body, 13)[0]
                mode_name = {1: "OneSided", 2: "TwoSided", 3: "Symmetric"}.get(mode)
                feature["operation"] = {"stored_code": operation, "kind": operation_name or "Unknown"}
                feature["extent"] = {"stored_code": mode, "mode": mode_name or "Unknown"}
                if operation_name is None or mode_name is None:
                    unknown.append({"object_id": feature["object_id"], "reason": "Unrecognized operation or extent mode"})
                if mode == 3:
                    distance_mode = body[123]
                    feature["extent"]["distance_convention"] = {
                        1: "FullLength", 2: "HalfLength"
                    }.get(distance_mode, "Unknown")
                    feature["extent"]["stored_distance_convention"] = distance_mode
                if "AlongDistance" in roles:
                    feature["extent"]["side_one_distance_cm"] = [p["raw_float64"] for p in roles["AlongDistance"]]
                elif mode == 1:
                    # Through-all was observed here, but other non-distance
                    # conditions have not been differentiated. Do not guess.
                    feature["extent"]["side_one_condition"] = "NonDistanceUnresolved"
                    unknown.append({"object_id": feature["object_id"], "reason": "Non-distance end condition not differentiated"})
                if "AgainstDistance" in roles:
                    feature["extent"]["side_two_distance_cm"] = [p["raw_float64"] for p in roles["AgainstDistance"]]
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
    return {"unresolved": unknown, "scope": "Observed extrusion fields and revolve angles only; no body regeneration"}
