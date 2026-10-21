"""Stored body-cache vertices through explicit identifier joins and placements."""

from decode_placement import transform_point


def decode_body_placement(bindings, assembly, asm_summary):
    streams = {s["member"]: s for s in asm_summary["streams"]}
    roots = [o for o in assembly["native_occurrences"] if o["parent_collection_object_id"] is None]
    bodies, unresolved = [], []
    for mapping in bindings["decoded"]:
        stream = streams.get(mapping["history_blob_member"], {})
        graphs = {g["body_index"]: g for g in stream.get("topology", {}).get("body_graphs", [])}
        initial_validation = mapping.get("initial_geometry_validation")
        if (initial_validation and initial_validation.get("initial_geometry_complete") is True
                and initial_validation.get("whole_token_stream_complete") is False):
            graphs = {g["body_index"]: g for g in initial_validation.get("validated_initial_geometry_body_graphs", [])}
        for entry in mapping["bindings"]:
            try:
                body = graphs.get(entry.get("asm_body_index"))
                if body is None or "component_object_id" not in entry:
                    raise ValueError("Typed ASM BODY identifier association or explicit component owner unresolved")
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
                               "history_blob_member": mapping["history_blob_member"], "asm_body_index": body["body_index"],
                               "asm_stored_entity_id": entry["asm_stored_entity_id"],
                               "association_status": entry["association_status"],
                               "lifecycle_status": entry["lifecycle_status"],
                               "component_vertex_positions_cm": points,
                               "placements": [{"path": p["path"], "component_to_world_matrix": p["world_transform"],
                                               "world_vertex_positions_cm": [transform_point(p["world_transform"], v) for v in points]}
                                              for p in paths],
                               "coordinate_scope": "Observed Fusion component-coordinate convention; ASM header scale not applied",
                               "geometry_scope": "Vertices only; curved extrema, full trimmed surfaces and body regeneration not covered"})
                if initial_validation:
                    bodies[-1]["initial_geometry_validation"] = {
                        key: value for key, value in initial_validation.items()
                        if key != "validated_initial_geometry_body_graphs"}
                if entry.get("historical_component_context"):
                    cached = bodies[-1]
                    cached["historical_component_context"] = entry["historical_component_context"]
                    cached["coordinate_scope"] = "Historical component association composed with stored occurrence caches; historic and current world placements unresolved"
                    for placement in cached["placements"]:
                        placement["component_to_stored_occurrence_cache_matrix"] = placement.pop("component_to_world_matrix")
                        placement["stored_occurrence_cache_vertex_positions_cm"] = placement.pop("world_vertex_positions_cm")
                        placement["world_placement_status"] = "Stored occurrence-cache context only; historical occurrence transforms and current visibility unresolved"
            except (ValueError, KeyError, IndexError) as error:
                unresolved.append({"native_body_object_id": entry["native_body_object_id"], "reason": str(error)})
    return {"bodies": bodies, "unresolved": unresolved,
            "scope": "Typed same-blob BODY identifier joins composed through stored occurrence caches; current body lifecycle unresolved"}


def label_joint_cache_placements(assembly, body_placement, features):
    """Keep unsolved occurrence caches distinct from joint-solved world output."""
    status = 'Joint kinematics not applied; stored occurrence caches do not establish solved placement'
    assembly['joint_kinematics_status'] = status
    assembly['scope'] = 'Native assembly ownership and stored occurrence caches; joint-solved placement unavailable'
    assembly['limitations'].append(status)
    for occurrence in assembly['native_occurrences']:
        occurrence['placement_status'] = status

    def sketch_cache(sketch):
        if 'sketch_to_world_matrix' in sketch:
            sketch['sketch_to_stored_occurrence_cache_matrix'] = sketch.pop('sketch_to_world_matrix')
        sketch['scope'] = 'Coordinates through stored occurrence caches; native joint solving not applied'

    for path in assembly['occurrence_paths']:
        if 'world_transform' in path:
            path['stored_occurrence_cache_transform'] = path.pop('world_transform')
        path['placement_status'] = status
        for sketch in path['sketches']:
            sketch_cache(sketch)
    for sketch in assembly['root_sketches']:
        sketch_cache(sketch)
    for feature in features:
        if feature['kind'] == 'Sketch' and 'placement' in feature:
            feature['placement']['scope'] = 'Native parent component; occurrence caches do not include joint solving'
    body_placement['joint_kinematics_status'] = status
    body_placement['scope'] = 'Typed same-blob BODY identifier joins through stored occurrence caches; no solved joint placement or final-body lifecycle'
    for body in body_placement['bodies']:
        for placement in body['placements']:
            if 'component_to_world_matrix' in placement:
                placement['component_to_stored_occurrence_cache_matrix'] = placement.pop('component_to_world_matrix')
            if 'world_vertex_positions_cm' in placement:
                placement['stored_occurrence_cache_vertex_positions_cm'] = placement.pop('world_vertex_positions_cm')
            placement['world_placement_status'] = status
            if body.get('historical_component_context'):
                placement['world_placement_status'] += '; historical occurrence transforms and current visibility unresolved'
