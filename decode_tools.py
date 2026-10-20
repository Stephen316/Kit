"""Observed modeling-tool controls and typed inputs; geometry remains partial."""

import struct

from decode_placement import rigid_matrix
from decode_selection import known_construction_entities
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
from decode_combine import decode_combine
from decode_sweep import decode_sweep
from decode_thicken import decode_thicken
from decode_emboss import decode_emboss
from decode_draft import decode_draft
from decode_circular_patterns import decode_circular_pattern
from decode_loft import decode_loft
from decode_boundary_fill import decode_boundary_fill


def decode_tools(data, records, features):
    supported = {"Sweep", "Loft", "CircularPattern", "Combine", "Draft", "Move", "Thicken", "Hole",
                 "Scale", "Mirror", "Shell", "RectangularPattern", "Fillet", "Chamfer", "SplitBody",
                 "OffsetFaces", "ReplaceFace", "DeleteFace", "SurfacePatch", "SurfaceOffset", "SurfaceStitch",
                 "Unstitch", "ReverseNormal", "SurfaceDeleteFace", "Pipe", "Thread",
                 "SurfaceExtend", "SurfaceUntrim", "SurfaceRuled", "SurfaceTrim", "PathPattern", "BoundaryFill", "Emboss"}
    decoded, unresolved = [], []
    axes = known_construction_entities(data, records, features)
    for feature in features:
        kind = feature["kind"]
        if kind not in supported:
            continue
        record = next(r for r in records if r.start == feature["record_offset"])
        body = data[record.body:record.end]
        try:
            settings = {}
            if kind == "Emboss":
                settings = decode_emboss(data, records, body, feature, features)
            elif kind == "BoundaryFill":
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
                settings = decode_combine(data, records, body, feature)
            elif kind == "CircularPattern":
                settings = decode_circular_pattern(data, records, body, feature, axes, features)
            elif kind == "Sweep":
                settings = decode_sweep(data, records, body, feature, features)
            elif kind == "Loft":
                settings = decode_loft(data, records, body, feature, features)
            elif kind == "Draft":
                settings = decode_draft(data, records, body, feature, axes)
            elif kind == "Thicken":
                settings = decode_thicken(data, records, body, feature)
            feature["tool_settings"] = settings
            feature["decode_level"] = "Observed tool settings and numeric parameters; geometric inputs remain partial"
            decoded.append({"object_id": feature["object_id"], "kind": kind})
        except (ValueError, KeyError, IndexError, struct.error) as error:
            unresolved.append({"object_id": feature["object_id"], "kind": kind, "reason": str(error)})
    return {"decoded": decoded, "unresolved": unresolved,
            "scope": "Observed settings only; no general input body/face/edge reconstruction"}
