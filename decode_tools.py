"""Observed extra modeling-tool settings; input bodies/topology remain unresolved."""

import math
import struct

from decode_placement import rigid_matrix
from decode_selection import known_construction_entities, resolve_native_selection
from decode_sketch import numbers, reference
from decode_holes import decode_hole
from decode_body_tools import decode_body_tool
from decode_patterns import decode_rectangular_pattern
from decode_edge_tools import decode_edge_tool
from decode_split import decode_split
from decode_face_tools import decode_face_tool
from decode_surface_tools import decode_surface_tool
from decode_pipe import decode_pipe
from decode_threads import decode_thread
from decode_path_patterns import decode_path_pattern
from decode_boundary_fill import decode_boundary_fill


def decode_tools(data, records, features):
    supported = {"Sweep", "Loft", "CircularPattern", "Combine", "Draft", "Move", "Thicken", "Hole",
                 "Scale", "Mirror", "Shell", "RectangularPattern", "Fillet", "Chamfer", "SplitBody",
                 "OffsetFaces", "ReplaceFace", "DeleteFace", "SurfacePatch", "SurfaceOffset", "SurfaceStitch",
                 "Unstitch", "ReverseNormal", "SurfaceDeleteFace", "Pipe", "Thread",
                 "SurfaceExtend", "SurfaceUntrim", "SurfaceRuled", "SurfaceTrim", "PathPattern", "BoundaryFill"}
    decoded, unresolved = [], []
    axes = known_construction_entities(data, records, features)
    for feature in features:
        kind = feature["kind"]
        if kind not in supported:
            continue
        record = next(r for r in records if r.start == feature["record_offset"])
        body = data[record.body:record.end]
        roles = {}
        for parameter in feature["parameters"]:
            roles.setdefault(parameter["role"], []).append(parameter)

        def parameter(role):
            choices = roles.get(role, [])
            if len(choices) != 1:
                raise ValueError("Missing or ambiguous tool parameter: "+role)
            return choices[0]

        try:
            settings = {}
            if kind == "BoundaryFill":
                settings = decode_boundary_fill(data, records, body, feature, axes)
            elif kind == "PathPattern":
                settings = decode_path_pattern(data, records, body, feature, features)
            elif kind == "Thread":
                settings = decode_thread(data, records, body, feature)
            elif kind == "Pipe":
                settings = decode_pipe(data, records, body, feature, features)
            elif kind in ("SurfacePatch", "SurfaceOffset", "SurfaceStitch", "Unstitch", "ReverseNormal", "SurfaceDeleteFace",
                          "SurfaceExtend", "SurfaceUntrim", "SurfaceRuled", "SurfaceTrim"):
                settings = decode_surface_tool(data, records, body, feature, axes)
            elif kind in ("OffsetFaces", "ReplaceFace", "DeleteFace"):
                settings = decode_face_tool(data, records, body, feature, axes)
            elif kind == "SplitBody":
                settings = decode_split(data, records, body, feature, axes)
            elif kind in ("Fillet", "Chamfer"):
                settings = decode_edge_tool(data, records, body, feature)
            elif kind == "RectangularPattern":
                settings = decode_rectangular_pattern(data, records, body, feature, axes)
            elif kind in ("Scale", "Mirror", "Shell"):
                settings = decode_body_tool(data, records, body, feature, axes)
            elif kind == "Hole":
                settings = decode_hole(data, records, body, feature)
            elif kind == "Move":
                if body[:2] != b"\0\0":
                    raise ValueError("Unrecognized move prefix")
                backend_id = reference(body, 2)
                choices = []
                for backend in records:
                    if backend.object_id != backend_id:
                        continue
                    chunk = data[backend.body:backend.end]
                    if len(chunk) != 237 or chunk[:24] != b"\0"*24:
                        continue
                    if struct.unpack_from("<I", chunk, 24)[0] != 5 or chunk[28] != 0:
                        continue
                    if reference(chunk, 164) != feature["object_id"] or reference(chunk, 226) != feature["object_id"]:
                        continue
                    choices.append(rigid_matrix(numbers(chunk, 29, 16)))
                if len(choices) != 1:
                    raise ValueError("Free-move transform unresolved or ambiguous")
                settings = {"definition": "FreeMove", "transform": choices[0],
                            "matrix_order": "row-major; column-vector multiplication", "translation_units": "cm",
                            "transform_record_object_id": backend_id}
            elif kind == "Combine":
                if body[:2] != b"\0\0" or body[10] not in (0, 1):
                    raise ValueError("Unrecognized combine prefix")
                code = struct.unpack_from("<I", body, 2)[0]
                if code not in (0, 1, 2):
                    raise ValueError("Unrecognized combine operation")
                settings = {"operation": {0: "Join", 1: "Cut", 2: "Intersect"}[code],
                            "stored_operation_code": code, "keep_tool_bodies": bool(body[10])}
            elif kind == "CircularPattern":
                quantity, angle = parameter("countU"), parameter("TotalAngle")
                if quantity["raw_float64"] < 2 or not quantity["raw_float64"].is_integer():
                    raise ValueError("Unsupported pattern quantity")
                control_id = reference(body, 6)
                choices = []
                for control in records:
                    if control.object_id != control_id:
                        continue
                    chunk = data[control.body:control.end]
                    if len(chunk) < 150 or chunk[:2] != b"\0\0" or chunk[2] not in (0, 1):
                        continue
                    if reference(chunk, 3) != angle["binding_object_id"]:
                        continue
                    if reference(chunk, len(chunk)-37) != quantity["binding_object_id"]:
                        continue
                    if reference(chunk, len(chunk)-26) != feature["object_id"]:
                        continue
                    axis_id = reference(chunk, 14)
                    selection = resolve_native_selection(data, records, axis_id, axes)
                    choices.append({"quantity": int(quantity["raw_float64"]),
                                    "total_angle_radians": angle["raw_float64"],
                                    "total_angle_degrees": math.degrees(angle["raw_float64"]),
                                    "is_symmetric": bool(chunk[2]), "axis_selection_record_object_id": axis_id,
                                    "axis": selection, "control_record_object_id": control_id})
                if len(choices) != 1:
                    raise ValueError("Pattern control record unresolved or ambiguous")
                settings = choices[0]
            elif kind == "Sweep":
                fraction = parameter("AlongDistance")
                if fraction["display_units"] != "" or not 0 <= fraction["raw_float64"] <= 1:
                    raise ValueError("Unsupported sweep path fraction")
                settings = {"path_fraction": fraction["raw_float64"],
                            "twist_angle_radians": parameter("TwistAngle")["raw_float64"],
                            "taper_angle_radians": parameter("TaperAngle")["raw_float64"]}
                code = struct.unpack_from("<I", body, 6)[0]
                settings["operation"] = "NewBody" if code == 4 else "Unknown"
                settings["stored_operation_code"] = code
            elif kind == "Loft":
                if body[:10] != b"\0\x01\0\0\0\0\x01\x01\x01\x01":
                    raise ValueError("Unrecognized basic loft prefix")
                count = struct.unpack_from("<I", body, 54)[0]
                if not 2 <= count <= 1024:
                    raise ValueError("Unsupported loft section count")
                sections = [reference(body, 58+i*11) for i in range(count)]
                code = struct.unpack_from("<I", body, 10)[0]
                settings = {"section_count": count, "section_input_record_object_ids": sections,
                            "operation": "NewBody" if code == 4 else "Unknown", "stored_operation_code": code,
                            "section_selection_status": "Exact profile contours unresolved"}
            elif kind == "Draft":
                settings = {"angle_one_radians": parameter("Angle1")["raw_float64"],
                            "angle_two_radians": parameter("Angle2")["raw_float64"],
                            "definition_status": "Draft mode and face selection unresolved"}
            elif kind == "Thicken":
                code = struct.unpack_from("<I", body, 7)[0]
                settings = {"thickness_cm": parameter("Thickness")["raw_float64"],
                            "operation": "NewBody" if code == 4 else "Unknown", "stored_operation_code": code,
                            "definition_status": "Face selection and sidedness unresolved"}
            feature["tool_settings"] = settings
            feature["decode_level"] = "Observed tool settings and numeric parameters; geometric inputs remain partial"
            decoded.append({"object_id": feature["object_id"], "kind": kind})
        except (ValueError, KeyError, IndexError, struct.error) as error:
            unresolved.append({"object_id": feature["object_id"], "kind": kind, "reason": str(error)})
    return {"decoded": decoded, "unresolved": unresolved,
            "scope": "Observed settings only; no general input body/face/edge reconstruction"}
