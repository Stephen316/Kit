"""Observed modeling-tool controls and typed inputs; geometry remains partial."""

import struct

from decode_selection import known_construction_entities
from decode_holes import decode_hole
from decode_body_tools import decode_body_tool
from decode_rectangular_pattern_modes import decode_rectangular_pattern_modes
from decode_edge_tools import decode_edge_tool
from decode_split import decode_split
from decode_split_face import decode_split_face
from decode_face_tools import decode_face_tool
from decode_surface_tools import decode_surface_tool
from decode_pipe import decode_pipe
from decode_threads import decode_thread
from decode_path_patterns import decode_path_pattern
from decode_path_pattern_composites import decode_path_pattern_composites
from decode_combine import decode_combine
from decode_sweep import decode_sweep
from decode_thicken import decode_thicken
from decode_emboss import decode_emboss
from decode_draft import decode_draft
from decode_circular_patterns import decode_circular_pattern
from decode_loft import decode_loft
from decode_move import decode_move
from decode_boundary_fill import decode_boundary_fill


def decode_tools(data, records, features):
    supported = {"Sweep", "Loft", "CircularPattern", "Combine", "Draft", "Move", "Thicken", "Hole",
                 "Scale", "Mirror", "Shell", "RectangularPattern", "Fillet", "Chamfer", "SplitBody", "SplitFace",
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
                try:
                    settings = decode_path_pattern(data, records, body, feature, features)
                except (ValueError, KeyError, IndexError, struct.error) as single_error:
                    try:
                        settings = decode_path_pattern_composites(data, records, body, feature, features)
                    except (ValueError, KeyError, IndexError, struct.error) as composite_error:
                        raise ValueError("Unsupported PathPattern variant; single path: "+str(single_error)
                                         +"; composite path: "+str(composite_error)) from composite_error
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
            elif kind == "SplitFace":
                settings = decode_split_face(data, records, body, feature, axes, features)
            elif kind in ("Fillet", "Chamfer"):
                settings = decode_edge_tool(data, records, body, feature)
            elif kind == "RectangularPattern":
                settings = decode_rectangular_pattern_modes(data, records, body, feature, axes, features)
            elif kind in ("Scale", "Mirror", "Shell"):
                settings = decode_body_tool(data, records, body, feature, axes)
            elif kind == "Hole":
                settings = decode_hole(data, records, body, feature)
            elif kind == "Move":
                settings = decode_move(data, records, body, feature, axes, features)
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
