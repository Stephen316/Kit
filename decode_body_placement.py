"""Observed component/world vertices for identity-normalized native body caches."""

from decode_placement import transform_point


def decode_body_placement(bindings, assembly, asm_summary):
    streams = {s["member"]: s for s in asm_summary["streams"]}
    roots = [o for o in assembly["native_occurrences"] if o["parent_collection_object_id"] is None]
    bodies, unresolved = [], []
    for mapping in bindings["decoded"]:
        stream = streams.get(mapping["history_blob_member"], {})
        graphs = {g["body_index"]: g for g in stream.get("topology", {}).get("body_graphs", [])}
        for entry in mapping["bindings"]:
            try:
                body = graphs.get(entry.get("candidate_asm_body_index"))
                if body is None or "component_object_id" not in entry:
                    raise ValueError("Body root candidate or explicit component owner unresolved")
                if not body.get("body_transform_is_identity"):
                    raise ValueError("Non-identity or unknown body transform is not validated")
                owner = entry["component_object_id"]
                paths = [p for p in assembly["occurrence_paths"] if p["component_object_id"] == owner]
                if len(roots) == 1 and roots[0]["component_object_id"] == owner:
                    paths = [{"path": "", "world_transform": roots[0]["local_transform"]}]+paths
                if not paths:
                    raise ValueError("Body component has no resolved assembly placement")
                points = body["raw_vertex_positions"]
                bodies.append({"native_body_object_id": entry["native_body_object_id"], "name": entry.get("name"),
                               "component_object_id": owner, "component_name": entry.get("component_name"),
                               "history_blob_member": mapping["history_blob_member"], "candidate_asm_body_index": body["body_index"],
                               "association_status": entry["association_status"],
                               "component_vertex_positions_cm": points,
                               "placements": [{"path": p["path"], "component_to_world_matrix": p["world_transform"],
                                               "world_vertex_positions_cm": [transform_point(p["world_transform"], v) for v in points]}
                                              for p in paths],
                               "coordinate_scope": "Observed Fusion component-coordinate convention; ASM header scale not applied",
                               "geometry_scope": "Vertices only; curved extrema, full trimmed surfaces and body regeneration not covered"})
            except (ValueError, KeyError, IndexError) as error:
                unresolved.append({"native_body_object_id": entry["native_body_object_id"], "reason": str(error)})
    return {"bodies": bodies, "unresolved": unresolved,
            "scope": "Conditional body-root candidates composed through decoded local occurrence paths"}
