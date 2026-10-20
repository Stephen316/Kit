"""Observed angular revolve modes and variable-length angle/axis references."""

import math
import struct

from decode_extrude import optional_reference
from decode_sketch import attributes, reference


def decode_revolve(body, feature):
    if body[0] != 0 or body[1] not in (0, 1):
        raise ValueError("Unsupported revolve prefix")
    cursor = attributes(body, 2)[1] if body[1] else 2
    operation, extent_code = struct.unpack_from("<II", body, cursor)
    operations = {1: "Join", 2: "Cut", 3: "Intersect", 4: "NewBody"}
    if operation not in operations or extent_code != 2 or body[cursor+8] != 0:
        raise ValueError("Unsupported revolve operation or extent layout")
    project, solid, symmetric, two_sided = body[cursor+9:cursor+13]
    if any(flag not in (0, 1) for flag in (project, solid, symmetric, two_sided)) or (symmetric and two_sided):
        raise ValueError("Unsupported revolve flags")
    against_id, cursor = optional_reference(body, cursor+13)
    along_id, cursor = optional_reference(body, cursor)
    axis_id = reference(body, cursor)
    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}

    def angle(identity, role):
        parameter = bindings.get(identity)
        if parameter is None or parameter["role"] != role:
            raise ValueError("Revolve angle binding does not resolve: "+role)
        return parameter["raw_float64"]

    along = angle(along_id, "AlongAngle")
    if bool(symmetric or two_sided) != (against_id is not None):
        raise ValueError("Revolve sidedness and against-angle reference disagree")
    mode = "Symmetric" if symmetric else "TwoSided" if two_sided else "OneSided"
    settings = {"mode": mode, "angle_radians": along, "angle_degrees": math.degrees(along),
                "along_angle_binding_object_id": along_id, "is_symmetric": bool(symmetric),
                "axis_selection_record_object_id": axis_id, "axis_selection": "Undecoded",
                "is_full_turn": math.isclose(abs(along), 2*math.pi, abs_tol=1e-10) if mode == "OneSided" else None}
    if against_id is not None:
        against = angle(against_id, "AgainstAngle")
        if symmetric and not math.isclose(against, along, abs_tol=1e-10):
            raise ValueError("Symmetric revolve angle bindings disagree")
        settings.update(against_angle_radians=against, against_angle_degrees=math.degrees(against),
                        against_angle_binding_object_id=against_id,
                        angle_scope="Separate stored along/against angles; combined full-turn classification unresolved")
    return {"operation": {"stored_code": operation, "kind": operations[operation]},
            "is_solid": bool(solid), "is_project_axis": bool(project), "revolve": settings}
