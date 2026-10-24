"""Observed scale, mirror and shell modes; selected body topology is partial."""

import math

from decode_extrude import optional_reference
from decode_selection import resolve_native_selection
from decode_sketch import attributes, numbers, reference


def decode_body_tool(data, records, body, feature, known, *, allowed_uniform_scale_prefixes=None):
    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}

    def value(identity, role):
        parameter = bindings.get(identity)
        if parameter is None or parameter["role"] != role:
            raise ValueError("Body-tool binding does not resolve: "+role)
        return parameter["raw_float64"]

    kind = feature["kind"]
    if kind == "Scale":
        if body[:2] != b"\0\0":
            raise ValueError("Unsupported scale prefix")
        cached = numbers(body, 2, 1)[0]
        point_id = reference(body, 10)
        factor_id, cursor = optional_reference(body, 21)
        if factor_id is not None:
            factor = value(factor_id, "ScaleFactor")
            prefixes = (bytes.fromhex("01000000000100000001000000"),) if allowed_uniform_scale_prefixes is None else allowed_uniform_scale_prefixes
            if not any(body[cursor:cursor+len(prefix)] == prefix for prefix in prefixes):
                raise ValueError("Unsupported uniform scale layout")
            if not math.isclose(cached, factor, abs_tol=1e-9):
                raise ValueError("Cached scale factor disagrees with parameter")
            settings = {"is_uniform": True, "factor": factor}
        else:
            if cached != 0 or body[cursor:cursor+6] != bytes.fromhex("010000000000"):
                raise ValueError("Unsupported nonuniform scale layout")
            settings = {"is_uniform": False,
                        "factors": [value(reference(body, cursor+6+11*i), role)
                                    for i, role in enumerate(("ScaleX", "ScaleY", "ScaleZ"))]}
        settings.update(point_selection_record_object_id=point_id,
                        point=resolve_native_selection(data, records, point_id, known),
                        input_selection_status="Input bodies/sketches unresolved")
        if settings["point"] is None:
            settings["point_selection_status"] = "Scale point reference unresolved"
        return settings
    if kind == "Shell":
        if body[:2] != b"\0\0" or body[2] not in (0, 1) or body[3] not in (0, 1):
            raise ValueError("Unsupported shell prefix")
        inside, cursor = optional_reference(body, 4)
        outside, cursor = optional_reference(body, cursor)
        return {"is_tangent_chain": bool(body[2]), "stored_shell_type": body[3],
                "shell_type": {0: "SharpOffset", 1: "RoundedOffset"}[body[3]],
                "inside_thickness_cm": value(inside, "innerThickness") if inside is not None else None,
                "outside_thickness_cm": value(outside, "outerThickness") if outside is not None else None,
                "input_selection_status": "Faces to remove and bodies unresolved"}
    if kind != "Mirror" or body[0] != 0 or body[1] not in (0, 1):
        raise ValueError("Unsupported body-tool layout")
    cursor = attributes(body, 2)[1] if body[1] else 2
    control_id = reference(body, cursor)
    candidates = []
    for record in records:
        if record.object_id != control_id or record.class_guid != "C444E6AD-33DC-4877-B037-A3A5518856B1":
            continue
        chunk = data[record.body:record.end]
        if len(chunk) != 133 or chunk[:2] != b"\0\0" or chunk[2] not in (0, 1):
            continue
        if reference(chunk, 107) != feature["object_id"]:
            continue
        plane_id = reference(chunk, 14)
        plane = resolve_native_selection(data, records, plane_id, known)
        if plane is not None and plane["entity"]["kind"] != "ConstructionPlane":
            raise ValueError("Mirror plane reference resolves to another entity kind")
        settings = {"is_combine": bool(chunk[2]), "stitch_tolerance_cm": value(reference(chunk, 3), "mirrorStitchTolerance"),
                    "plane_selection_record_object_id": plane_id, "plane": plane,
                    "control_record_object_id": control_id,
                    "input_selection_status": "Mirror input bodies/features and compute option unresolved"}
        if plane is None:
            settings["plane_selection_status"] = "Mirror plane reference unresolved"
        candidates.append(settings)
    if len(candidates) != 1:
        raise ValueError("Mirror control record unresolved or ambiguous")
    return candidates[0]
