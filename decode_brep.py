"""Observed ASM topology links and primitive geometry; cached bodies stay separate.

Field order was cross-referenced with the primary ezdxf ACIS entity definitions:
https://github.com/mozman/ezdxf/blob/master/src/ezdxf/acis/entities.py
Local Fusion samples establish the accepted token signatures and extra fields.
"""

from collections import Counter
import math


LINKS = {
    "body": {"first_lump": (3, "lump"), "first_wire": (4, "wire"), "transform": (5, "transform")},
    "lump": {"next_lump": (3, "lump"), "first_shell": (4, "shell"), "body": (5, "body")},
    "shell": {"next_shell": (3, "shell"), "subshell": (4, "subshell"), "first_face": (5, "face"),
              "first_wire": (6, "wire"), "lump": (7, "lump")},
    "face": {"next_face": (3, "face"), "first_loop": (4, "loop"), "shell": (5, "shell"),
             "subshell": (6, "subshell"), "surface": (7, "surface")},
    "loop": {"next_loop": (3, "loop"), "first_coedge": (4, "coedge"), "face": (5, "face")},
    "coedge": {"next_coedge": (3, "coedge"), "previous_coedge": (4, "coedge"),
               "partner": (5, "coedge"), "edge": (6, "edge"), "loop": (8, "loop"), "pcurve": (10, "curve")},
    "edge": {"start_vertex": (3, "vertex"), "end_vertex": (5, "vertex"),
             "first_coedge": (7, "coedge"), "curve": (8, "curve")},
    "vertex": {"first_edge": (3, "edge"), "point": (5, "point")},
}


def decode_topology(parsed):
    if not parsed["complete_token_stream"]:
        return {"body_graphs": [], "unresolved": [{"reason": "ASM token stream incomplete"}], "nodes": []}
    records = parsed["records"]
    geometry_limit = next((i for i, r in enumerate(records) if r.get("record_kind") == "marker"), len(records))
    nodes, unresolved = {}, []

    def token(record, index, kinds):
        item = record["tokens"][index]
        if item["kind"] not in kinds:
            raise ValueError("Unexpected token kind at field "+str(index))
        return item["value"]

    def link(record, index, expected=None):
        target = token(record, index, ("pointer",))
        if target == -1:
            return None
        if not 0 <= target < geometry_limit:
            raise ValueError("ASM pointer outside initial geometry entity table")
        name = records[target]["name"]
        if expected and name != expected and not name.endswith("-"+expected):
            raise ValueError("ASM pointer target has unexpected type: "+name)
        return target

    def intervals(record, start, count):
        bounds, cursor = [], start
        for _ in range(count):
            finite = token(record, cursor, ("boolean_token",))
            cursor += 1
            bounds.append(token(record, cursor, ("double",)) if finite else None)
            if finite:
                cursor += 1
        if cursor != len(record["tokens"]):
            raise ValueError("Unsupported primitive interval trailer")
        return bounds

    geometry = {"point", "straight-curve", "ellipse-curve", "plane-surface"}
    sizes = {"body": (6,), "lump": (6,), "shell": (8,), "face": (10, 11), "loop": (6,),
             "coedge": (11,), "edge": (11,), "vertex": (6,), "point": (4,), "straight-curve": (7, 8, 9),
             "ellipse-curve": (9, 10, 11)}
    for record in records[:geometry_limit]:
        name = record["name"]
        if name not in LINKS and name not in geometry:
            continue
        try:
            if name in sizes and len(record["tokens"]) not in sizes[name]:
                raise ValueError("Unsupported observed entity field count")
            node = {"index": record["index"], "kind": name, "offset": record["offset"],
                    "attribute_index": link(record, 0), "stored_entity_id": token(record, 1, ("integer",)),
                    "pattern_index": link(record, 2, "pattern")}
            for field, (index, expected) in LINKS.get(name, {}).items():
                node[field+"_index"] = link(record, index, expected)
            if name == "face":
                node["is_reversed"] = token(record, 8, ("boolean_token",))
                node["is_double_sided"] = token(record, 9, ("boolean_token",))
                if node["is_double_sided"]:
                    node["stored_containment_flag"] = token(record, 10, ("boolean_token",))
                elif len(record["tokens"]) != 10:
                    raise ValueError("Unexpected single-sided face fields")
            elif name == "coedge":
                node["is_reversed"] = token(record, 7, ("boolean_token",))
                node["uninterpreted_field_9"] = token(record, 9, ("integer",))
            elif name == "edge":
                node.update(start_parameter=token(record, 4, ("double",)),
                            end_parameter=token(record, 6, ("double",)),
                            is_reversed=token(record, 9, ("boolean_token",)),
                            stored_trailing_text=token(record, 10, ("string",)))
            elif name == "vertex":
                node["uninterpreted_field_4"] = token(record, 4, ("integer",))
            elif name in geometry:
                node["raw_origin"] = token(record, 3, ("position_vector",))
                if name != "point":
                    direction = token(record, 4, ("direction_vector",))
                    if not math.isclose(sum(v*v for v in direction), 1., abs_tol=1e-9):
                        raise ValueError("Non-unit primitive direction/normal")
                    node["direction" if name == "straight-curve" else "normal"] = direction
                if name in ("ellipse-curve", "plane-surface"):
                    axis = token(record, 5, ("direction_vector",))
                    if not math.isclose(sum(x*y for x, y in zip(axis, direction)), 0., abs_tol=1e-9):
                        raise ValueError("Primitive reference axis is not perpendicular to normal")
                    node["stored_reference_axis"] = axis
                    if name == "ellipse-curve":
                        ratio = token(record, 6, ("double",))
                        major = math.sqrt(sum(v*v for v in axis))
                        if major <= 0 or not 0 < ratio <= 1:
                            raise ValueError("Unsupported ellipse radii")
                        node.update(raw_major_radius=major, raw_minor_radius=major*ratio,
                                    stored_axis_ratio=ratio)
                        node["parameter_interval"] = intervals(record, 7, 2)
                    else:
                        node["is_v_reversed"] = token(record, 6, ("boolean_token",))
                        bounds = intervals(record, 7, 4)
                        node.update(u_interval=bounds[:2], v_interval=bounds[2:])
                elif name == "straight-curve":
                    node["parameter_interval"] = intervals(record, 5, 2)
            nodes[record["index"]] = node
        except (ValueError, IndexError) as error:
            unresolved.append({"index": record["index"], "kind": name, "reason": str(error)})

    def get(index, expected):
        node = nodes.get(index)
        if node is None or node["kind"] != expected:
            raise ValueError("Required topology node unresolved: "+str(index))
        return node

    def chain(index, kind, next_field):
        result, seen = [], set()
        while index is not None:
            if index in seen or len(result) > 100000:
                raise ValueError("Cycle or excessive length in "+kind+" list")
            seen.add(index)
            node = get(index, kind)
            result.append(index)
            index = node[next_field+"_index"]
        return result

    graphs = []
    for root in list(nodes.values()):
        if root["kind"] != "body":
            continue
        try:
            if root["first_wire_index"] is not None:
                raise ValueError("Wire-body topology not implemented")
            lumps = chain(root["first_lump_index"], "lump", "next_lump")
            shells, faces, loops, coedges, edges, vertices = [], [], [], [], set(), set()
            for lump_id in lumps:
                lump = get(lump_id, "lump")
                if lump["body_index"] != root["index"]:
                    raise ValueError("Lump/body ownership is not reciprocal in this stored state")
                lump_shells = chain(lump["first_shell_index"], "shell", "next_shell")
                shells.extend(lump_shells)
                for shell_id in lump_shells:
                    shell = get(shell_id, "shell")
                    if shell["lump_index"] != lump_id or shell["subshell_index"] is not None or shell["first_wire_index"] is not None:
                        raise ValueError("Unsupported shell ownership/subshell/wire definition")
                    shell_faces = chain(shell["first_face_index"], "face", "next_face")
                    faces.extend(shell_faces)
                    for face_id in shell_faces:
                        face = get(face_id, "face")
                        if face["surface_index"] is None:
                            raise ValueError("Face has no surface reference")
                        if face["shell_index"] != shell_id or face["subshell_index"] is not None:
                            raise ValueError("Face/shell ownership is not reciprocal")
                        face_loops = chain(face["first_loop_index"], "loop", "next_loop")
                        loops.extend(face_loops)
                        for loop_id in face_loops:
                            loop = get(loop_id, "loop")
                            if loop["face_index"] != face_id:
                                raise ValueError("Loop/face ownership is not reciprocal")
                            first = loop["first_coedge_index"]
                            if first is None:
                                continue
                            current, seen = first, set()
                            while current not in seen:
                                seen.add(current)
                                coedge = get(current, "coedge")
                                if coedge["loop_index"] != loop_id:
                                    raise ValueError("Coedge/loop ownership is not reciprocal")
                                next_id = coedge["next_coedge_index"]
                                if get(next_id, "coedge")["previous_coedge_index"] != current:
                                    raise ValueError("Coedge next/previous links disagree")
                                partner = coedge["partner_index"]
                                if partner is not None and get(partner, "coedge")["edge_index"] != coedge["edge_index"]:
                                    raise ValueError("Partner coedges do not refer to the same edge")
                                edge = get(coedge["edge_index"], "edge")
                                edges.add(edge["index"])
                                for field in ("start_vertex_index", "end_vertex_index"):
                                    if edge[field] is not None:
                                        get(edge[field], "vertex")
                                        vertices.add(edge[field])
                                coedges.append(current)
                                current = next_id
                            if current != first:
                                raise ValueError("Coedge ring does not close at its first element")
            raw_positions = [get(get(v, "vertex")["point_index"], "point")["raw_origin"] for v in sorted(vertices)]
            counts = {"lump": len(lumps), "shell": len(shells), "face": len(faces), "loop": len(loops),
                      "coedge": len(coedges), "edge": len(edges), "vertex": len(vertices)}
            graphs.append({"body_index": root["index"], "counts": counts, "lump_indices": lumps,
                           "shell_indices": shells, "face_indices": faces, "loop_indices": loops,
                           "coedge_indices": coedges, "edge_indices": sorted(edges), "vertex_indices": sorted(vertices),
                           "raw_vertex_positions": raw_positions, "transform_index": root["transform_index"],
                           "surface_record_types": dict(Counter(records[nodes[f]["surface_index"]]["name"] for f in faces)),
                           "all_coedges_have_partners": bool(coedges) and all(nodes[c]["partner_index"] is not None for c in coedges),
                           "identity_status": "Stored body graph; final visible body mapping unresolved",
                           "coordinate_scope": "Raw ASM points; body transform and units/context not applied"})
        except (ValueError, KeyError, IndexError) as error:
            unresolved.append({"index": root["index"], "kind": "body_graph", "reason": str(error)})
    return {"nodes": list(nodes.values()), "body_graphs": graphs, "unresolved": unresolved,
            "initial_geometry_record_count": geometry_limit,
            "history_status": "History journal and trailing state records retained as tokens; excluded from topology graphs",
            "scope": "Observed reciprocal links within initial geometry entity tables; no history-state merging"}
