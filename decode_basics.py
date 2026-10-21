"""Experimental named-feature and parameter-reference decoding for Fusion.

Layouts are inferred from Fusion 2705.1.30 samples, not a complete schema.
Unknown fields remain unknown. Explicit feature controls, selections and ownership
links accompany partial cached ASM topology; general regeneration, persistent
topology mapping and native file writing remain unavailable.
"""

import argparse
import copy
from bisect import bisect_right
import json
from pathlib import Path
import re
import struct

from decode_parameters import decode_stream, read_string
from decode_parameter_tables import decode_parameter_tables
from decode_expression_dependencies import derive_expression_dependencies
from decode_sketch import decode_sketches
from decode_sketch_surface_constraints import decode_sketch_surface_constraints
from decode_sketch_mixed_patterns import decode_sketch_mixed_patterns
from decode_emboss_texts import decode_consumed_sketch_texts
from decode_pipe_edge_controls import inspect_pipe_edge_controls
from decode_pipe_vertex_contexts import inspect_pipe_auxiliary_vertex_context
from decode_sketch_text_controls import decode_sketch_text_controls
from decode_sketch_text_paths import decode_sketch_text_paths
from decode_sketch_coverage import decode_sketch_coverage
from decode_offset_details import decode_offset_details
from decode_sketch_projections import decode_sketch_projections
from decode_sketch_projection_families import decode_sketch_projection_families
from decode_face_boundary_projections import decode_face_boundary_projections
from decode_sketch_pattern_details import decode_sketch_pattern_details
from decode_dimension_controls import decode_dimension_controls
from decode_dimension_control_modes import decode_dimension_control_modes
from decode_tangent_dimension_caches import decode_tangent_dimension_caches
from decode_modeling import decode_modeling
from decode_placement import decode_placement
from decode_selection import decode_selections, known_construction_entities
from decode_revolve_axes import decode_revolve_axes
from decode_tools import decode_tools
from decode_hole_point_sources import decode_hole_point_sources
from decode_hole_supports import decode_hole_supports
from decode_boundary_fill_results import decode_boundary_fill_results
from decode_boundary_sculpt_provenance import decode_boundary_sculpt_provenance
from decode_pipe_paths import inspect_pipe_edge_path
from decode_pattern_placements import decode_pattern_placements
from fusion_archive import read_members
from fusion_records import Record, record_fragments
from fusion_metadata import design_records
from discover_features import discover_features
from decode_construction import decode_construction
from decode_plane_definitions import decode_plane_definitions
from decode_path_planes import decode_path_planes
from decode_construction_definitions import decode_construction_definitions
from decode_construction_modes import decode_construction_modes
from decode_construction_vertex_points import decode_construction_vertex_points
from decode_brep_edge_axes import decode_brep_edge_axes
from decode_profiles import decode_profiles
from decode_timeline import decode_timeline
from decode_timeline_state_details import decode_timeline_state_details
from decode_assembly import decode_assembly
from decode_occurrence_gate_attributes import occurrence_with_gate_attributes
from decode_dependencies import decode_dependencies
from asm_records import inspect_asm_members
from decode_body_bindings import decode_body_bindings
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_historical_body_components import decode_historical_body_components
from decode_selection_recipe_incidence import decode_selection_recipe_incidence
from decode_fpm_tracking import decode_fpm_selection_tracking
from decode_fpm_context_cache import decode_fpm_context_cache
from decode_asm_recipe_tags import inspect_pipe_recipe_tags
from decode_pipe_recipe_incidence import inspect_pipe_recipe_incidence
from decode_pipe_edge_limits import inspect_pipe_edge_limits
from decode_body_properties import decode_body_properties
from decode_body_selections import decode_body_selections
from decode_body_tool_selections import decode_body_tool_selections
from decode_component_creation import decode_component_creation
from decode_mirror_component_creations import decode_mirror_component_creations
from decode_pin_provenance import decode_pin_provenance
from decode_selection_context_recipes import decode_selection_context_recipes
from decode_selection_context_variants import decode_selection_context_variants
from decode_sketch_symmetric_indices import decode_sketch_symmetric_indices
from decode_scale_inputs import decode_scale_vertex_points
from decode_direct_body_features import decode_direct_body_features
from decode_copy_paste_occurrences import decode_copy_paste_occurrences
from decode_silhouette_splits import decode_silhouette_splits
from decode_silhouette_directions import decode_silhouette_directions
from decode_silhouette_line_contexts import decode_silhouette_line_contexts
from decode_remaining_body_inputs import decode_remaining_body_input, MIRROR_COMPONENT, MIRROR_DATUM
from decode_mirror_datum_outputs import decode_mirror_datum_outputs
from decode_mirror_datum_reflections import decode_mirror_datum_reflections
from decode_circular_placement_evidence import decode_circular_placement_evidence
from decode_fpm_partial_coverage import decode_fpm_partial_coverage
from decode_mirror_nested_occurrences import decode_mirror_nested_occurrences
from decode_special_fillets import decode_special_fillets
from decode_surface_extrudes import decode_surface_extrudes
from decode_body_mapping_variants import decode_body_mapping_variants
from decode_recipe_components import decode_recipe_components
from decode_body_property_variants import decode_body_collection_attribute_variants
from decode_text_literal_dependencies import derive_text_literal_dependencies
from decode_brep_recipes import decode_recipes
from decode_component_body_proxies import decode_component_body_proxies
from decode_combine import attach_combine_bodies
from decode_tool_body_inputs import decode_tool_body_inputs
from decode_body_placement import decode_body_placement, label_joint_cache_placements
from decode_joints import decode_joints, JOINT as NATIVE_JOINT_GUID, DEFINITION as JOINT_DEFINITION_GUID


def named_features(data, records):
    features = []
    starts = [r.start for r in records]
    labels = {"Sketch": "Sketch", "Extrude": "Extrude", "Revolve": "Revolve",
              "Fillet": "Fillet", "Chamfer": "Chamfer", "Shell": "Shell", "Hole": "Hole",
              "R-Pattern": "RectangularPattern", "Mirror": "Mirror", "Scale": "Scale",
              "WorkPlane": "ConstructionPlane", "Sweep": "Sweep", "Loft": "Loft",
              "C-Pattern": "CircularPattern", "Combine": "Combine", "Draft": "Draft",
              "Split": "SplitBody", "SplitFace": "SplitFace", "Move": "Move", "Thicken": "Thicken",
              "WorkAxis": "ConstructionAxis", "WorkPoint": "ConstructionPoint",
              "OffsetFaces": "OffsetFaces", "ReplaceFace": "ReplaceFace", "DeleteFace": "DeleteFace",
              "SurfacePatch": "SurfacePatch", "SurfaceOffset": "SurfaceOffset", "SurfaceStitch": "SurfaceStitch",
              "UnStitch": "Unstitch", "Reverse Normal": "ReverseNormal", "SurfaceDeleteFace": "SurfaceDeleteFace",
              "Pipe": "Pipe", "Thread": "Thread", "SurfaceExtend": "SurfaceExtend",
              "SurfaceUntrim": "SurfaceUntrim", "SurfaceRuled": "SurfaceRuled", "SurfaceTrim": "SurfaceTrim",
              "PathPattern": "PathPattern", "BoundaryFill": "BoundaryFill", "Emboss": "Emboss"}
    for label, kind in labels.items():
        marker = struct.pack("<I", len(label)) + label.encode("utf-16le")
        for match in re.finditer(re.escape(marker), data):
            index = bisect_right(starts, match.start()) - 1
            if index < 0:
                continue
            record = records[index]
            chunk = data[record.body:record.end]
            try:
                _, cursor = read_string(chunk, match.start() - record.body)
                stored_index = struct.unpack_from("<Q", chunk, cursor)[0]
                if stored_index >= 2**32:
                    continue
                item = {
                    "kind": kind, "object_id": record.object_id,
                    "native_kind_label": label,
                    "stored_index": stored_index, "record_offset": record.start,
                    "type_code": record.type_code, "parameters": [],
                    "class_guid": record.class_guid, "class_namespace": record.class_namespace,
                }
                if kind != "Sketch":
                    name, _ = read_string(chunk, cursor + 8)
                    item["name"] = name or None
                else:
                    # The sketch feature points to a separate named sketch object.
                    # A counted list of parameter bindings precedes that pointer.
                    count = struct.unpack_from("<I", chunk, 3)[0]
                    root_offset = 13 + count * 11
                    if count > 1024 or root_offset + 8 > len(chunk) or chunk[root_offset - 1] != 1:
                        continue
                    root_id = struct.unpack_from("<Q", chunk, root_offset)[0]
                    roots = []
                    for candidate in records:
                        if candidate.object_id != root_id:
                            continue
                        body = data[candidate.body:candidate.end]
                        if len(body) <= 28 or body[0] != 1:
                            continue
                        try:
                            name, _ = read_string(body, 28)
                            roots.append(name)
                        except (ValueError, UnicodeError, struct.error):
                            continue
                    if len(roots) != 1:
                        continue
                    item.update({"name": roots[0] or None, "sketch_object_id": root_id})
                features.append(item)
            except (ValueError, UnicodeError, struct.error):
                continue
    return sorted(features, key=lambda f: f["record_offset"])


def attach_parameters(data, records, features, parameters):
    by_id = {f["object_id"]: f for f in features}
    starts = [r.start for r in records]
    pending, attached = {}, set()
    for parameter in parameters:
        owner = parameter.get("binding_owner_object_id")
        if parameter.get("value_type") == "Text" and owner in by_id and by_id[owner]["kind"] == "Sketch":
            by_id[owner]["parameters"].append({
                **parameter, "binding_object_id": parameter["declared_binding_object_id"],
                "association": "Explicit sketch owner and reciprocal Text parameter binding with matching UTF16LE payload",
            })
            attached.add(parameter["role_offset"])
            continue
        index = bisect_right(starts, parameter["role_offset"]) - 1
        if index >= 0:
            pending.setdefault(records[index].object_id, []).append(parameter)
    for record in records:
        body = data[record.body:record.end]
        if len(body) not in (82, 85) or body[:6] != b"\x01\x01\0\0\0\x01":
            continue
        owner = struct.unpack_from("<Q", body, 6)[0]
        parameter_offset = 30 if len(body) == 85 else 27
        if body[parameter_offset - 1] != 1 or body[-11] != 1 or body[-2:] != b"\0\0":
            continue
        if struct.unpack_from("<Q", body, len(body) - 10)[0] != owner:
            continue
        parameter_id = struct.unpack_from("<Q", body, parameter_offset)[0]
        choices = pending.get(parameter_id, [])
        if owner not in by_id or len(choices) != 1:
            continue
        parameter = choices[0]
        if parameter.get("declared_binding_object_id", record.object_id) != record.object_id:
            continue
        raw_value = data[parameter["value_offset"]:parameter["value_offset"] + 8]
        if len(body) == 85:
            matches_value = body[21:29] == raw_value
        else:
            matches_value = body[21] == 1 and struct.unpack_from("<I", body, 22)[0] == parameter["raw_float64"]
        if not matches_value or parameter["role_offset"] in attached:
            continue
        by_id[owner]["parameters"].append({
            **parameter, "parameter_object_id": parameter_id,
            "binding_object_id": record.object_id, "binding_offset": record.start,
            "binding_value_representation": "float64" if len(body) == 85 else "tagged_uint32",
            "association": "explicit owner and parameter references with matching numeric payload",
        })
        attached.add(parameter["role_offset"])
    return [p for p in parameters if p["role_offset"] not in attached]


def sketch_references(data, records, features):
    by_feature = {f["object_id"]: f for f in features if f["kind"] in ("Extrude", "Revolve", "SurfacePatch")}
    by_sketch = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
    for record in records:
        body = data[record.body:record.end]
        if len(body) < 50 or body[-11] != 1 or body[-2:] != b"\0\0":
            continue
        owner = struct.unpack_from("<Q", body, len(body) - 10)[0]
        if owner not in by_feature:
            continue
        matches = []
        for offset in range(len(body) - 4):
            if body[offset:offset + 4] != b"\x24\0\0\0":
                continue
            try:
                namespace, cursor = read_string(body, offset)
                identity, _ = read_string(body, cursor)
            except (ValueError, UnicodeError, struct.error):
                continue
            if (not re.fullmatch(r"[0-9a-fA-F-]{36}", namespace)
                    or not identity.isascii() or not identity.isdecimal()):
                continue
            sketch = by_sketch.get(int(identity))
            if sketch:
                matches.append({
                    "sketch_object_id": int(identity), "feature_object_id": sketch["object_id"],
                    "name": sketch["name"], "reference_record_offset": record.start,
                    "namespace_text": namespace,
                    "scope": "observed sketch reference; selected contour is not decoded",
                })
        if len(matches) == 1:
            by_feature[owner].setdefault("sketch_reference_candidates", []).extend(matches)


def decode_basics(path, zstd_library=None):
    streams = []
    members = read_members(path, zstd_library)
    asm_summary = inspect_asm_members(members)
    for name, data in members.items():
        if not name.endswith("FusionDesignSegmentType1/BulkStream.dat"):
            continue
        records, record_index = design_records(data, members.get(name.replace("BulkStream.dat", "MetaStream.dat")))
        features = named_features(data, records)
        discovery_summary = discover_features(data, records, features, record_index)
        parameters, rejected = decode_stream(data, records)
        unbound = attach_parameters(data, records, features, parameters)
        sketch_references(data, records, features)
        sketch_summary = decode_sketches(data, records, features)
        surface_constraint_summary = decode_sketch_surface_constraints(data, records, features)
        surface_sketches = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
        recovered_surface_ids = set()
        for key, items in (("geometry", surface_constraint_summary["additional_geometry"]),
                           ("constraints", surface_constraint_summary["constraints"])):
            for item in items:
                sketch = surface_sketches[item["sketch_object_id"]]
                if not any(existing["object_id"] == item["object_id"] for existing in sketch[key]):
                    sketch[key].append(copy.deepcopy(item))
                recovered_surface_ids.add(item["object_id"])
        for key in ("unsupported_curves", "unknown_constraint_codes"):
            sketch_summary[key] = [item for item in sketch_summary[key] if item["object_id"] not in recovered_surface_ids]
        sketch_summary["tool_constraints"]["unresolved"] = [item for item in sketch_summary["tool_constraints"]["unresolved"]
                                                           if item["object_id"] not in recovered_surface_ids]
        curved_pattern_summary = decode_sketch_mixed_patterns(data, records, features)
        pattern_coverage_summary = decode_sketch_symmetric_indices(data, records, features)
        curved_sketches = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
        recovered_curve_ids = set()
        for geometry in curved_pattern_summary["additional_geometry"]:
            sketch = curved_sketches[geometry["sketch_object_id"]]
            if not any(g["object_id"] == geometry["object_id"] for g in sketch["geometry"]):
                sketch["geometry"].append(copy.deepcopy(geometry))
                recovered_curve_ids.add(geometry["object_id"])
        recovered_pattern_ids = set()
        for pattern in curved_pattern_summary["patterns"]+pattern_coverage_summary["patterns"]:
            sketch = curved_sketches[pattern["sketch_object_id"]]
            if not any(c["object_id"] == pattern["object_id"] for c in sketch["constraints"]):
                sketch["constraints"].append(copy.deepcopy(pattern))
                sketch_summary["tool_constraints"]["decoded"].append({
                    "object_id": pattern["object_id"], "kind": pattern["kind"],
                    "sketch_object_id": pattern["sketch_object_id"]})
            recovered_pattern_ids.add(pattern["object_id"])
        sketch_summary["tool_constraints"]["unresolved"] = [u for u in sketch_summary["tool_constraints"]["unresolved"]
                                                           if u["object_id"] not in recovered_pattern_ids]
        sketch_summary["unsupported_curves"] = [u for u in sketch_summary["unsupported_curves"]
                                                if u["object_id"] not in recovered_curve_ids]
        sketch_summary["tool_constraints"]["scope"] += "; "+curved_pattern_summary["scope"]
        sketch_summary["tool_constraints"]["scope"] += "; "+pattern_coverage_summary["scope"]
        sketch_text_summary = decode_sketch_text_controls(data, records, features)
        path_text_summary = decode_sketch_text_paths(data, records, features)
        consumed_text_summary = decode_consumed_sketch_texts(data, records, features)
        text_by_id = {t["object_id"]: t for t in sketch_text_summary["texts"]}
        for text in path_text_summary["texts"]:
            text_by_id.setdefault(text["object_id"], text)
        for text in consumed_text_summary["texts"]:
            text_by_id.setdefault(text["object_id"], text)
        sketch_text_summary["texts"] = sorted(text_by_id.values(), key=lambda t: t["record_offset"])
        text_unresolved = {}
        for item in sketch_text_summary["unresolved"]+path_text_summary["unresolved"]+consumed_text_summary["unresolved"]:
            if item["object_id"] in text_by_id:
                continue
            if item["object_id"] not in text_unresolved:
                text_unresolved[item["object_id"]] = dict(item)
            elif item["reason"] != text_unresolved[item["object_id"]]["reason"]:
                text_unresolved[item["object_id"]]["additional_reason"] = item["reason"]
        sketch_text_summary["unresolved"] = list(text_unresolved.values())
        sketch_text_summary["scope"] += "; "+path_text_summary["scope"]
        sketch_text_summary["scope"] += "; "+consumed_text_summary["scope"]
        text_sketches = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
        for text in sketch_text_summary["texts"]:
            text_sketches[text["sketch_object_id"]].setdefault("texts", []).append(text)
        sketch_coverage_summary = decode_sketch_coverage(data, records, features, record_index, sketch_summary)
        offset_detail_summary = decode_offset_details(data, records, features)
        sketch_pattern_summary = decode_sketch_pattern_details(data, records, features)
        dimension_control_summary = decode_dimension_controls(data, records, features)
        dimension_mode_summary = decode_dimension_control_modes(data, records, features, dimension_control_summary)
        dimensions_by_id = {d["object_id"]: d for f in features if f["kind"] == "Sketch" for d in f["dimensions"]}
        tangent_cache_summary = decode_tangent_dimension_caches(data, records, features, dimension_control_summary)
        for cache in tangent_cache_summary["decoded"]:
            dimensions_by_id[cache["object_id"]]["geometry_cache"] = cache
        annotations_by_id = {a["object_id"]: a for a in dimension_control_summary["decoded"]}
        for mode in dimension_mode_summary["decoded"]:
            dimensions_by_id[mode["object_id"]].update(is_driving=mode["is_driving"], driving_status=mode["driving_status"])
            annotations_by_id[mode["object_id"]].update(is_driving=mode["is_driving"],
                                                      stored_reference_flag=mode["stored_reference_flag"],
                                                      driving_status=mode["driving_status"],
                                                      position_scope=mode["annotation_position_evidence"])
        projection_summary = decode_sketch_projections(data, records, features)
        projection_families = decode_sketch_projection_families(data, records, features)
        face_boundary_summary = decode_face_boundary_projections(data, records, features)
        # One controller can explicitly name multiple outputs, such as two
        # circle/plane intersections. Preserve each output relationship.
        projection_keys = {(r["controller_object_id"], r["output_cache"]["object_id"])
                           for r in projection_summary["relationships"]}
        for relationship in projection_families["relationships"]+face_boundary_summary["relationships"]:
            key = relationship["controller_object_id"], relationship["output_cache"]["object_id"]
            if key not in projection_keys:
                projection_summary["relationships"].append(relationship)
                projection_keys.add(key)
        resolved_projection_ids = {key[0] for key in projection_keys}
        projection_unresolved = {}
        for item in projection_summary["unresolved"]+projection_families["unresolved"]+face_boundary_summary["unresolved"]:
            if item["object_id"] in resolved_projection_ids:
                continue
            if item["object_id"] not in projection_unresolved:
                projection_unresolved[item["object_id"]] = dict(item)
            elif item["reason"] != projection_unresolved[item["object_id"]]["reason"]:
                projection_unresolved[item["object_id"]]["additional_reason"] = item["reason"]
        projection_summary["unresolved"] = list(projection_unresolved.values())
        projection_summary["scope"] += "; "+projection_families["scope"]
        if face_boundary_summary["relationships"]:
            projection_summary["scope"] += "; "+face_boundary_summary["scope"]
        for relationship in projection_summary["relationships"]:
            target = next(f for f in features if f["object_id"] == relationship["target_feature_object_id"])
            output = next((g for g in target["geometry"] if g["object_id"] == relationship["output_cache"]["object_id"]), None)
            if output is not None:
                output["projection_reference"] = {"controller_object_id": relationship["controller_object_id"],
                                                  "method": relationship["method"], "is_linked": relationship["is_linked"],
                                                  "scope": "Explicit native projection relationship; source details in sketch_projections"}
        profile_summary = decode_profiles(data, records, features)
        modeling_summary = decode_modeling(data, records, features)
        surface_extrude_summary = decode_surface_extrudes(data, records, features)
        surface_extrude_ids, open_profile_ids = set(), set()
        for extrusion in surface_extrude_summary["decoded"]:
            feature = next(f for f in features if f["object_id"] == extrusion["feature_object_id"])
            feature.update(extrusion["settings"])
            feature["surface_extrusion_source"] = {k: v for k, v in extrusion.items() if k not in ("settings", "feature_object_id")}
            feature["decode_level"] = "Observed one-sided sheet extrusion controls and explicit sketch source; surface regeneration unsupported"
            surface_extrude_ids.add(feature["object_id"])
            if extrusion["profile"].get("profile_kind") == "SketchOpenProfile":
                feature["open_profile_selection"] = extrusion["profile"]
                open_profile_ids.add(feature["object_id"])
                profile_summary["decoded"].append({"feature_object_id": feature["object_id"], "kind": "SketchOpenProfile",
                                                   "descriptor_object_id": extrusion["profile"]["descriptor_object_id"], "curve_count": 1})
        modeling_summary["unresolved"] = [item for item in modeling_summary["unresolved"]
                                              if item["object_id"] not in surface_extrude_ids
                                              or item["reason"] != "Unsupported extrusion start prefix"]
        profile_summary["unresolved"] = [item for item in profile_summary["unresolved"]
                                             if item["feature_object_id"] not in open_profile_ids
                                             or item["reason"] != "Profile source reference is unresolved"]
        placement_summary = decode_placement(data, records, features)
        construction_summary = decode_construction(data, records, features)
        plane_definition_summary = decode_plane_definitions(data, records, features)
        path_plane_summary = decode_path_planes(data, records, features)
        recovered_path_planes = {item["feature_object_id"] for item in path_plane_summary["definitions"]}
        for definition in path_plane_summary["definitions"]:
            plane = next(f for f in features if f["object_id"] == definition["feature_object_id"])
            plane.update(definition["cached_geometry"], plane_definition_details=definition,
                         decode_level="Observed endpoint PathDistance plane definition and explicit fitted-spline source",
                         selection_status="Explicit sketch-ID/curve-tag path source with reciprocal supports",
                         unresolved_inputs=["General path-distance mapping, offsets and construction regeneration"])
        plane_definition_summary["definitions"].extend(path_plane_summary["definitions"])
        plane_definition_summary["unresolved"] = [item for item in plane_definition_summary["unresolved"]
                                                     if item["feature_object_id"] not in recovered_path_planes]
        if recovered_path_planes:
            plane_definition_summary["scope"] += "; "+path_plane_summary["scope"]
        construction_definition_summary = decode_construction_definitions(data, records, features)
        construction_mode_summary = decode_construction_modes(data, records, features)
        construction_vertex_summary = decode_construction_vertex_points(data, records, features)
        brep_axis_summary = decode_brep_edge_axes(data, records, features)
        recovered_axis_ids = {item["feature_object_id"] for item in brep_axis_summary["definitions"]}
        for definition in brep_axis_summary["definitions"]:
            feature = next(f for f in features if f["object_id"] == definition["feature_object_id"])
            feature.update(definition["cached_geometry"], construction_definition=definition,
                           decode_level="Observed native axis cache and owned BRep edge definition; construction regeneration unsupported",
                           selection_status="Explicit owned BRep edge recipe and historical source body",
                           unresolved_inputs=["Exact persistent source edge geometry and ASM identity"])
        construction_mode_summary["definitions"].extend(brep_axis_summary["definitions"])
        if recovered_axis_ids:
            construction_mode_summary["scope"] += "; "+brep_axis_summary["scope"]
        construction_mode_summary["unresolved"] = [item for item in construction_mode_summary["unresolved"]
                                                      if item["feature_object_id"] not in recovered_axis_ids]
        resolved_vertex_ids = {d["feature_object_id"] for d in construction_vertex_summary["definitions"]}
        construction_mode_summary["unresolved"] = [u for u in construction_mode_summary["unresolved"]
                                                   if u["feature_object_id"] not in resolved_vertex_ids]
        additional_construction_definitions = construction_mode_summary["definitions"]+construction_vertex_summary["definitions"]
        resolved_construction_modes = {d["feature_object_id"] for d in additional_construction_definitions}
        construction_summary["unresolved"] = [u for u in construction_summary["unresolved"]
                                               if u["object_id"] not in resolved_construction_modes]
        cached_construction_ids = {d["object_id"] for d in construction_summary["decoded"]}
        construction_summary["decoded"].extend(
            {"object_id": d["feature_object_id"], "kind": d["kind"]}
            for d in additional_construction_definitions if d["feature_object_id"] not in cached_construction_ids)
        construction_definition_summary["unresolved"] = [u for u in construction_definition_summary["unresolved"]
                                                          if u["feature_object_id"] not in resolved_construction_modes]
        placement_summary["decoded_construction_planes"] = sum(
            f["kind"] == "ConstructionPlane" and "plane_to_component_matrix" in f for f in features)
        placement_summary["scope"] = "Observed rigid sketch transforms and native construction-plane caches; explicit definitions reported separately"
        selection_summary = decode_selections(data, records, features)
        revolve_axis_summary = decode_revolve_axes(data, records, features)
        selection_summary["scope"] += "; "+revolve_axis_summary["scope"]
        revolve_features = {f["object_id"]: f for f in features if f["kind"] == "Revolve"}
        for selected_axis in revolve_axis_summary["decoded"]:
            revolve_features[selected_axis["feature_object_id"]]["revolve"].update(
                axis=selected_axis["axis"], axis_selection="Observed native axis source reference and geometry decoded")
            selection_summary["resolved"].append({"feature_object_id": selected_axis["feature_object_id"],
                                                   "selection_object_id": selected_axis["selection_object_id"]})
        resolved_axis_keys = {(a["feature_object_id"], a["selection_object_id"]) for a in revolve_axis_summary["decoded"]}
        selection_summary["unresolved"] = [a for a in selection_summary["unresolved"]
                                             if (a["feature_object_id"], a["selection_object_id"]) not in resolved_axis_keys]
        tool_summary = decode_tools(data, records, features)
        hole_point_summary = decode_hole_point_sources(data, records, features)
        for sources in hole_point_summary["decoded"]:
            hole = next(f for f in features if f["object_id"] == sources["feature_object_id"])
            hole["tool_settings"].update(point_sources=sources["point_sources"], association_status=sources["association"])
        pipe_provenance_summary = {"partial": [], "unresolved": [],
                                   "scope": "Separate source provenance and observed edge Pipe controls; bounded cached source geometry may decode through serialized recipe incidence, full settings remain partial"}
        pipe_vertex_summary = {"decoded": [], "unresolved": [],
                               "scope": "Typed auxiliary vertex contexts only; Pipe closure, geometry and full settings unresolved"}
        for pipe in features:
            if pipe["kind"] != "Pipe" or "tool_settings" in pipe:
                continue
            pipe_record = next(r for r in records if r.start == pipe["record_offset"])
            try:
                try:
                    source = inspect_pipe_edge_controls(data, records, data[pipe_record.body:pipe_record.end], pipe, features)
                except (ValueError, KeyError, IndexError, struct.error):
                    source = inspect_pipe_edge_path(data, records, data[pipe_record.body:pipe_record.end], pipe, features)
                if source.get("native_has_auxiliary_point_selector"):
                    try:
                        vertex_context = inspect_pipe_auxiliary_vertex_context(
                            data, records, data[pipe_record.body:pipe_record.end], pipe, features, source_evidence=source)
                        source["auxiliary_point_selection"]["vertex_context_evidence"] = vertex_context
                        pipe_vertex_summary["decoded"].append(vertex_context)
                    except (ValueError, KeyError, IndexError, struct.error) as error:
                        pipe_vertex_summary["unresolved"].append({"feature_object_id": pipe["object_id"], "reason": str(error)})
                pipe_provenance_summary["partial"].append(source)
            except (ValueError, KeyError, IndexError, struct.error) as error:
                pipe_provenance_summary["unresolved"].append({"feature_object_id": pipe["object_id"], "reason": str(error)})
        pattern_placement_summary = decode_pattern_placements(data, records, features)
        assembly_summary = decode_assembly(data, records, features, occurrence_decoder=occurrence_with_gate_attributes)
        joint_summary = decode_joints(data, records, assembly_summary, features)
        resolved_joint_definitions = set()
        for joint in joint_summary["decoded"]:
            feature = next(f for f in features if f["object_id"] == joint["definition_object_id"])
            if feature["class_guid"] == JOINT_DEFINITION_GUID:
                feature["kind"] = "Joint"
                feature["name"] = feature.get("name") or joint["name"]
                feature["joint_settings"] = joint
                feature["decode_level"] = "Observed native joint origins, motion controls and limits; joint solving not applied"
                resolved_joint_definitions.add(feature["object_id"])
        discovery_summary["unsupported_features"] = [f for f in discovery_summary["unsupported_features"]
                                                     if f["object_id"] not in resolved_joint_definitions]
        discovery_summary["unsupported_feature_count"] = len(discovery_summary["unsupported_features"])
        discovery_summary["class_decoded_joint_definition_count"] = len(resolved_joint_definitions)
        timeline_state_summary = decode_timeline_state_details(data, records, features)
        recovered_states = {item["object_id"]: item["state"] for item in timeline_state_summary["states"]}
        timeline_summary = decode_timeline(data, records, features, feature_state_overrides=recovered_states)
        dependency_summary = decode_dependencies(data, records, features, assembly_summary)
        component_creation_summary = decode_component_creation(data, records, features, assembly_summary)
        mirror_creation_summary = decode_mirror_component_creations(data, records, features, assembly_summary)
        mirror_creation_ids = {item["feature_object_id"] for item in mirror_creation_summary["decoded"]}
        component_creation_summary["mirror_owned_creations"] = mirror_creation_summary["decoded"]
        component_creation_summary["unresolved"] = [item for item in component_creation_summary["unresolved"]
                                                       if item["feature_object_id"] not in mirror_creation_ids]
        timeline_state_summary = decode_timeline_state_details(data, records, features, assembly=assembly_summary,
                                                               component_creation=component_creation_summary)
        timeline_aliases = {(item["history_record_object_id"], item["native_history_entry_object_id"]): item
                            for item in timeline_state_summary["occurrence_aliases"]}
        for sequence in timeline_summary["sequences"]:
            for entry in sequence["visible_entries"]:
                for visible in [entry]+entry.get("children", []):
                    alias = timeline_aliases.get((sequence["history_record_object_id"], visible["object_id"]))
                    if alias is not None:
                        visible["occurrence_creation"] = alias
        copy_paste_summary = decode_copy_paste_occurrences(data, records, features, assembly_summary, component_creation_summary)
        pin_provenance_summary = decode_pin_provenance(data, records, assembly_summary, features)
        decoded_assembly_feature_ids = set()
        feature_by_id = {f["object_id"]: f for f in features}
        for creation in component_creation_summary["decoded"]:
            feature = feature_by_id[creation["feature_object_id"]]
            feature.update(kind="CreateComponent", component_creation=creation,
                           decode_level="Observed explicit component creation and historical occurrence placement; replay unsupported")
            snapshot = feature_by_id.get(creation["snapshot_object_id"])
            if snapshot is not None:
                snapshot["component_creation_snapshot"] = creation
            decoded_assembly_feature_ids.add(feature["object_id"])
        for creation in mirror_creation_summary["decoded"]:
            feature = feature_by_id[creation["feature_object_id"]]
            feature.update(kind="CreateComponent", mirror_component_creation=creation,
                           decode_level="Observed Mirror-owned component creation and stored occurrence correspondence; no snapshot or solved placement inferred")
            decoded_assembly_feature_ids.add(feature["object_id"])
        for pin in pin_provenance_summary["decoded"]:
            feature = feature_by_id[pin["feature_object_id"]]
            feature.update(kind="Pin", pin_provenance=pin,
                           decode_level="Observed explicit Pin occurrence provenance; current grounded state unresolved")
            decoded_assembly_feature_ids.add(feature["object_id"])
        for copied in copy_paste_summary["decoded"]:
            feature = feature_by_id[copied["feature_object_id"]]
            feature.update(kind="CopyPaste", copy_paste_occurrence=copied,
                           decode_level="Observed explicit source/created occurrence links and historical caches; general copying/replay unsupported")
            decoded_assembly_feature_ids.add(feature["object_id"])
        discovery_summary["unsupported_features"] = [f for f in discovery_summary["unsupported_features"]
                                                     if f["object_id"] not in decoded_assembly_feature_ids]
        discovery_summary["unsupported_feature_count"] = len(discovery_summary["unsupported_features"])
        discovery_summary["class_decoded_component_creation_count"] = len(component_creation_summary["decoded"])+len(mirror_creation_ids)
        discovery_summary["class_decoded_pin_provenance_count"] = len(pin_provenance_summary["decoded"])
        discovery_summary["class_decoded_copy_paste_count"] = len(copy_paste_summary["decoded"])
        body_property_summary = decode_body_properties(data, records, assembly_summary)
        body_property_variant_summary = decode_body_collection_attribute_variants(data, records, assembly_summary, body_property_summary)
        existing_collection_ids = {item["object_id"] for item in body_property_summary["collections"]}
        body_property_summary["collections"].extend(item for item in body_property_variant_summary["decoded_collections"]
                                                    if item["object_id"] not in existing_collection_ids)
        body_ownership_updates = {item["object_id"]: item for item in body_property_variant_summary["body_ownership_updates"]}
        for body in body_property_summary["bodies"]:
            if body["object_id"] in body_ownership_updates:
                body.update(body_ownership_updates[body["object_id"]])
                body.pop("ownership_status", None)
        recovered_collection_ids = {item["object_id"] for item in body_property_variant_summary["decoded_collections"]}
        body_property_summary["unresolved"] = [item for item in body_property_summary["unresolved"]
                                                  if item["kind"] != "BodyCollection" or item["object_id"] not in recovered_collection_ids]
        body_mapping_variant_summary = decode_body_mapping_variants(data, records, name, asm_summary, body_property_summary)
        recovered_body_names = {item["object_id"]: item for item in body_mapping_variant_summary["passive_body_name_updates"]}
        for body in body_property_summary["bodies"]:
            if body["object_id"] in recovered_body_names:
                body.update(recovered_body_names[body["object_id"]])
        body_property_summary["unresolved"] = [item for item in body_property_summary["unresolved"]
                                                  if item["kind"] != "BodyName" or item["object_id"] not in recovered_body_names]
        body_selection_summary = decode_body_selections(data, records, body_property_summary)
        component_body_summary = decode_component_body_proxies(data, records, body_selection_summary, assembly_summary)
        body_selection_summary["selection_proxies"].extend(component_body_summary["decoded"])
        resolved_component_proxies = {item["selection_record_object_id"] for item in component_body_summary["decoded"]}
        body_selection_summary["unresolved"] = [item for item in body_selection_summary["unresolved"]
                                                if item["kind"] != "BodySelectionProxy"
                                                or item["object_id"] not in resolved_component_proxies]
        body_selection_summary["unresolved"].extend(component_body_summary["unresolved"])
        body_selection_summary["component_context_scope"] = component_body_summary["scope"]
        hole_support_summary = decode_hole_supports(data, records, features, body_selection_summary)
        for inputs in hole_support_summary["decoded"]:
            hole = feature_by_id[inputs["feature_object_id"]]
            settings = hole.get("tool_settings")
            if settings is not None:
                settings.update(support_selection=inputs["support"],
                                position_support_inputs=inputs["position_support_inputs"],
                                center_edge_selection=inputs["center_edge_input"],
                                native_body_input=inputs["native_body_input"],
                                core_input_provenance=inputs["core_input"],
                                support_selection_status=inputs["support_selection_status"])
                settings["extent"].update(inputs["extent_inputs"])
        boundary_result_summary = decode_boundary_fill_results(data, records)
        for results in boundary_result_summary["decoded"]:
            boundary = feature_by_id.get(results["feature_object_id"])
            if boundary is not None and "tool_settings" in boundary:
                boundary["tool_settings"].update({key: results[key] for key in (
                    "owned_result_body_count", "owned_result_bodies", "result_selection_bodies",
                    "explicit_result_body_count", "result_selection_proxy_object_ids", "result_selection_scope")})
        special_fillet_summary = decode_special_fillets(data, records, features, body_selection_summary)
        original_tool_ids = {item["object_id"] for item in tool_summary["decoded"]}
        special_fillet_summary["unresolved"] = [item for item in special_fillet_summary["unresolved"]
                                                  if item["feature_object_id"] not in original_tool_ids]
        special_fillet_ids = set()
        for fillet in special_fillet_summary["decoded"]:
            feature = feature_by_id[fillet["feature_object_id"]]
            feature.update(tool_settings={k: v for k, v in fillet.items() if k not in ("feature_object_id", "kind")},
                           decode_level="Observed full-round/rule fillet controls and source roles; exact topology and regeneration unsupported")
            special_fillet_ids.add(feature["object_id"])
            if feature["object_id"] not in original_tool_ids:
                tool_summary["decoded"].append({"object_id": feature["object_id"], "kind": "Fillet"})
        tool_summary["unresolved"] = [item for item in tool_summary["unresolved"] if item["object_id"] not in special_fillet_ids]
        selection_context_summary = decode_selection_context_recipes(data, records, body_selection_summary)
        selection_context_variant_summary = decode_selection_context_variants(data, records, body_selection_summary,
                                                                              selection_context_summary)
        recovered_context_ids = {item["descriptor_object_id"] for item in selection_context_variant_summary["contexts"]}
        selection_context_summary["contexts"].extend(selection_context_variant_summary["contexts"])
        context_variant_failures = {item["descriptor_object_id"]: item for item in selection_context_variant_summary["unresolved"]}
        selection_context_summary["unresolved"] = [item for item in selection_context_summary["unresolved"]
                                                      if item["descriptor_object_id"] not in recovered_context_ids]
        for item in selection_context_summary["unresolved"]:
            if item["descriptor_object_id"] in context_variant_failures:
                item["additional_reason"] = context_variant_failures[item["descriptor_object_id"]]["reason"]
        if recovered_context_ids:
            selection_context_summary["scope"] += "; "+selection_context_variant_summary["scope"]
        direct_body_summary = decode_direct_body_features(data, records, body_selection_summary)
        silhouette_summary = decode_silhouette_splits(data, records, features, body_selection_summary)
        silhouette_direction_summary = decode_silhouette_directions(data, records, features, body_selection_summary)
        silhouette_line_summary = decode_silhouette_line_contexts(data, records, features, body_selection_summary,
                                                                 source_summary=silhouette_direction_summary)
        silhouette_direction_by_id = {item["feature_object_id"]: item for item in silhouette_direction_summary["decoded"]}
        for cache in silhouette_line_summary["decoded"]:
            silhouette_direction_by_id[cache["feature_object_id"]]["view_direction"]["entity"]["cached_source_line_context"] = cache
        original_silhouette_ids = {item["feature_object_id"] for item in silhouette_summary["decoded"]}
        extended_silhouette_ids = {item["feature_object_id"] for item in silhouette_direction_summary["decoded"]}
        extended_silhouettes = {item["feature_object_id"]: item for item in silhouette_direction_summary["decoded"]}
        silhouette_summary["decoded"] = [extended_silhouettes.get(item["feature_object_id"], item)
                                          for item in silhouette_summary["decoded"]]
        silhouette_summary["decoded"].extend(item for item in silhouette_direction_summary["decoded"]
                                              if item["feature_object_id"] not in original_silhouette_ids)
        silhouette_summary["unresolved"] = [item for item in silhouette_summary["unresolved"]
                                               if item["feature_object_id"] not in extended_silhouette_ids]
        silhouette_direction_summary["unresolved"] = [item for item in silhouette_direction_summary["unresolved"]
                                                         if item["feature_object_id"] not in original_silhouette_ids]
        if extended_silhouette_ids:
            silhouette_summary["scope"] += "; "+silhouette_direction_summary["scope"]
        direct_body_ids = set()
        for direct_body in direct_body_summary["decoded"]:
            feature = feature_by_id.get(direct_body["feature_object_id"])
            if feature is not None:
                feature.update(kind=direct_body["kind"], direct_body_feature=direct_body,
                               decode_level="Observed explicit body provenance; general direct editing, lifecycle and regeneration unsupported")
                direct_body_ids.add(feature["object_id"])
        silhouette_ids = set()
        for split in silhouette_summary["decoded"]:
            feature = feature_by_id[split["feature_object_id"]]
            feature.update(kind="SilhouetteSplit", tool_settings={k: v for k, v in split.items() if k not in ("feature_object_id", "kind")},
                           decode_level="Observed SilhouetteSplit operation and historical source selections; silhouette geometry/regeneration unsupported")
            silhouette_ids.add(feature["object_id"])
            tool_summary["decoded"].append({"object_id": feature["object_id"], "kind": "SilhouetteSplit"})
        discovery_summary["unsupported_features"] = [f for f in discovery_summary["unsupported_features"]
                                                     if f["object_id"] not in direct_body_ids|silhouette_ids]
        discovery_summary["unsupported_feature_count"] = len(discovery_summary["unsupported_features"])
        discovery_summary["class_decoded_direct_body_feature_count"] = len(direct_body_ids)
        discovery_summary["class_decoded_silhouette_split_count"] = len(silhouette_ids)
        attach_combine_bodies(features, body_selection_summary)
        remaining_input_summary = {"decoded_settings": [], "partial": [], "unresolved": [],
                                   "scope": "Observed additional feature/face/Sketch inputs and separate occurrence/datum provenance; unavailable controls and regeneration remain unresolved"}
        known_input_entities = known_construction_entities(data, records, features)
        mirror_datum_summary = {"decoded": [], "scope": "Observed explicit datum Mirror output ownership and oriented plane caches; regeneration unavailable"}
        mirror_nested_summary = {"decoded": [], "scope": "Observed two-level occurrence Mirror routes and parent ownership; stored caches, no assembly solving or replay"}
        resolved_input_ids = set()
        for feature in features:
            settings = feature.get("tool_settings", {})
            candidate = (feature["class_guid"] in (MIRROR_COMPONENT, MIRROR_DATUM)
                         or feature["kind"] == "Mirror" and settings.get("input_kind") is None
                         or feature["kind"] == "Scale" and "tool_settings" not in feature)
            if not candidate:
                continue
            source_record = next(r for r in records if r.start == feature["record_offset"])
            try:
                try:
                    inputs = decode_remaining_body_input(data, records, data[source_record.body:source_record.end],
                                                         feature, known_input_entities, features, assembly_summary)
                except (ValueError, KeyError, IndexError, UnicodeError, struct.error):
                    if feature["class_guid"] == MIRROR_DATUM:
                        provenance = decode_mirror_datum_outputs(data, records, data[source_record.body:source_record.end],
                                                                feature, known_input_entities)
                        mirror_datum_summary["decoded"].append(provenance)
                    elif feature["class_guid"] == MIRROR_COMPONENT:
                        provenance = decode_mirror_nested_occurrences(data, records, data[source_record.body:source_record.end],
                                                                      feature, known_input_entities, assembly_summary)
                        mirror_nested_summary["decoded"].append(provenance)
                    else:
                        raise
                    inputs = {"status": "PartialProvenance", "provenance": provenance}
                if inputs["status"] == "DecodedSettings":
                    feature.update(tool_settings=inputs["settings"],
                                   decode_level="Observed additional input identities and available controls; topology and regeneration unsupported")
                    remaining_input_summary["decoded_settings"].append({"feature_object_id": feature["object_id"], "settings": inputs["settings"]})
                    resolved_input_ids.add(feature["object_id"])
                    if not any(item["object_id"] == feature["object_id"] for item in tool_summary["decoded"]):
                        tool_summary["decoded"].append({"object_id": feature["object_id"], "kind": feature["kind"]})
                else:
                    feature["input_provenance"] = inputs["provenance"]
                    remaining_input_summary["partial"].append(inputs["provenance"])
            except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
                remaining_input_summary["unresolved"].append({"feature_object_id": feature["object_id"], "reason": str(error)})
        tool_summary["unresolved"] = [item for item in tool_summary["unresolved"] if item["object_id"] not in resolved_input_ids]
        datum_reflection_summary = decode_mirror_datum_reflections(data, records, features, assembly_summary)
        datum_reflections = {row['feature_object_id']: row for row in datum_reflection_summary['decoded']}
        for identity, reflection in datum_reflections.items():
            feature_by_id[identity].update(datum_reflection=reflection,
                decode_level='Observed datum Mirror inputs/output and component reflection cache; unavailable controls and general replay unresolved',
                unresolved_inputs=reflection['unresolved_controls'])
        for item in tool_summary['unresolved']:
            if item['object_id'] in datum_reflections:
                item['reason'] = 'Datum Mirror inputs/output and reflected cache decoded; combine/stitch control semantics and general regeneration remain unresolved'
        scale_vertex_summary = decode_scale_vertex_points(data, records, features, body_selection_summary)
        for selected_point in scale_vertex_summary["decoded"]:
            feature_by_id[selected_point["feature_object_id"]]["tool_settings"].update(
                point=selected_point["point"], point_selection_status=selected_point["point_selection_status"])
        body_tool_selection_summary = decode_body_tool_selections(data, records, features, body_selection_summary)
        for selected_inputs in body_tool_selection_summary["decoded"]:
            feature = next(f for f in features if f["object_id"] == selected_inputs["feature_object_id"])
            feature["tool_settings"].update(selected_inputs["settings"])
        tool_body_summary = decode_tool_body_inputs(data, records, features, body_selection_summary)
        for item in tool_body_summary["decoded"]:
            feature = next(f for f in features if f["object_id"] == item["feature_object_id"])
            feature["body_input_associations"] = item["body_selection_groups"]
        recipe_summary = decode_recipes(data, records)
        recipe_component_summary = decode_recipe_components(data, records, recipe_summary)
        existing_recipe_ids = {item["object_id"] for item in recipe_summary["recipes"]}
        recipe_summary["recipes"].extend(item for item in recipe_component_summary["recipes"] if item["object_id"] not in existing_recipe_ids)
        recovered_recipe_ids = {item["object_id"] for item in recipe_component_summary["recipes"]}
        recipe_summary["unresolved"] = [item for item in recipe_summary["unresolved"] if item["object_id"] not in recovered_recipe_ids]
        if recovered_recipe_ids:
            recipe_summary["scope"] += "; "+recipe_component_summary["scope"]
        body_binding_summary = decode_body_bindings(data, records, name, asm_summary, body_property_summary)
        existing_mapping_ids = {item["mapping_record_object_id"] for item in body_binding_summary["decoded"]}
        body_binding_summary["decoded"].extend(item for item in body_mapping_variant_summary["decoded"]
                                                 if item["mapping_record_object_id"] not in existing_mapping_ids)
        recovered_mapping_ids = {item["mapping_record_object_id"] for item in body_mapping_variant_summary["decoded"]}
        body_binding_summary["unresolved"] = [item for item in body_binding_summary["unresolved"] if item["object_id"] not in recovered_mapping_ids]
        body_identifier_summary = decode_body_asm_identifiers(data, records, name, members, body_binding_summary)
        invalidated_mapping_ids = set(body_identifier_summary["invalidate_ordinal_candidates_for_mapping_ids"])
        keyed_mappings = {item["mapping_record_object_id"]: item for item in body_identifier_summary["decoded"]}
        for mapping in body_binding_summary["decoded"]:
            mapping_id = mapping["mapping_record_object_id"]
            if mapping_id not in invalidated_mapping_ids:
                continue
            for field in ("auxiliary_declared_roots", "root_table_status", "initial_geometry_validation"):
                if field in keyed_mappings.get(mapping_id, {}):
                    mapping[field] = keyed_mappings[mapping_id][field]
            patches = {entry["native_body_object_id"]: entry for entry in keyed_mappings.get(mapping_id, {}).get("bindings", [])}
            for entry in mapping["bindings"]:
                entry.pop("candidate_asm_body_index", None)
                entry["association_status"] = "ASM body identifier association unresolved; ordinal candidate withdrawn"
                if entry["native_body_object_id"] in patches:
                    entry.update(patches[entry["native_body_object_id"]])
                    entry["handle_scope"] = entry["identifier_scope"]
            mapping["scope"] = "Explicit native body/blob mapping; only validated same-blob typed BODY identifier joins supply ASM roots"
        body_binding_summary["scope"] = "Native body/blob mapping and observed typed per-blob BODY identifiers; final-body lifecycle unresolved"
        historical_component_summary = decode_historical_body_components(
            data, records, body_binding_summary, assembly_summary)
        for patch in historical_component_summary["decoded"]:
            mapping = next(m for m in body_binding_summary["decoded"]
                           if m["mapping_record_object_id"] == patch["mapping_record_object_id"])
            entry = next(b for b in mapping["bindings"]
                         if b["native_body_object_id"] == patch["native_body_object_id"])
            entry.update({key: patch[key] for key in
                          ("component_object_id", "component_name", "historical_component_context")})
        selection_recipe_incidence_summary = decode_selection_recipe_incidence(
            data, records, features, name, members, body_identifier_summary, body_selection_summary)
        fpm_selection_tracking_summary = decode_fpm_selection_tracking(
            data, records, features, name, members, body_identifier_summary, body_selection_summary)
        fpm_body_tracking_summary = decode_fpm_partial_coverage(data, records, name, members, body_identifier_summary)
        for correspondence in fpm_body_tracking_summary['associations']:
            target = feature_by_id.get(correspondence['feature_object_id'])
            if target is not None:
                target.setdefault('fpm_body_correspondences', []).append(correspondence)
        # A complete successful BODY-kind bridge can account for an edge-only
        # reader's rejected attributes. Never clear a mapping on grammar coverage
        # alone, or when a valid edge attribute still needs the old tracking pass.
        if fpm_body_tracking_summary['associations']:
            from decode_fpm_tracking import decode_fpm_attributes
            covered_mappings = set()
            for coverage in fpm_body_tracking_summary['coverage']:
                mapping_id, blob_member = coverage['mapping_record_object_id'], coverage['history_blob_member']
                successful = {row['FPM_attribute']['attribute_record_index']
                    for row in fpm_body_tracking_summary['associations']
                    if row['mapping_record_object_id'] == mapping_id and row['history_blob_member'] == blob_member}
                try:
                    legacy = decode_fpm_attributes(members[blob_member])
                except (ValueError, KeyError, IndexError, UnicodeError, struct.error):
                    # Optional coverage reconciliation cannot invalidate the
                    # separately qualified BODY associations or old diagnostic.
                    continue
                rejected_ids = {row['attribute_record_index'] for row in legacy['unresolved']}
                if rejected_ids and rejected_ids <= successful and not legacy['attributes']:
                    covered_mappings.add(mapping_id)
            fpm_selection_tracking_summary['unresolved'] = [row for row in fpm_selection_tracking_summary['unresolved']
                if row.get('mapping_record_object_id') not in covered_mappings
                or row.get('reason') != 'Incomplete FPM attribute coverage prevents unique literal correspondence']
        circular_cache_summary = decode_circular_placement_evidence(data, records, features, name, members, body_binding_summary)
        for evidence in circular_cache_summary['decoded']:
            feature_by_id[evidence['feature_object_id']]['circular_placement_evidence'] = evidence
        fpm_context_cache_summary = decode_fpm_context_cache(data, records, fpm_selection_tracking_summary)
        boundary_sculpt_summary = decode_boundary_sculpt_provenance(
            data, records, name, members, features, body_binding_summary)
        for provenance in boundary_sculpt_summary["decoded"]:
            feature_by_id[provenance["feature_object_id"]]["boundary_fill_sculpt_provenance"] = provenance
        pipe_tag_summary = {"decoded": [], "unresolved": [],
                            "scope": "Explicit same-asset native recipe/ASM naming candidates; duplicate owners and whole-recipe semantics stay unresolved"}
        pipe_incidence_summary = {"decoded": [], "unresolved": [],
                                  "scope": "Observed named-face recipe operands and reciprocal topology identify cached source edges; complete Pipe operation and path direction remain unresolved"}
        pipe_limit_summary = {"decoded": [], "unresolved": [],
                              "scope": "Observed single-edge Pipe active fractions and named source-start vertex; path direction and resulting partial geometry remain unresolved"}
        for source in pipe_provenance_summary["partial"]:
            pipe = feature_by_id[source["feature_object_id"]]
            pipe_record = next(r for r in records if r.start == pipe["record_offset"])
            try:
                naming = inspect_pipe_recipe_tags(data, records, data[pipe_record.body:pipe_record.end], pipe,
                                                  features, name, members, body_identifier_summary, source_evidence=source)
                pipe_tag_summary["decoded"].append(naming)
                source["asm_recipe_naming_candidates"] = naming
            except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
                pipe_tag_summary["unresolved"].append({"feature_object_id": pipe["object_id"], "reason": str(error)})
                continue
            try:
                incidence = inspect_pipe_recipe_incidence(
                    data, records, data[pipe_record.body:pipe_record.end], pipe, features,
                    name, members, body_identifier_summary, source_evidence=source, tag_evidence=naming)
                pipe_incidence_summary["decoded"].append(incidence)
                source["cached_source_edge_incidence"] = incidence
                pipe["pipe_cached_source_edge"] = incidence
            except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
                pipe_incidence_summary["unresolved"].append({"feature_object_id": pipe["object_id"], "reason": str(error)})
                continue
            try:
                limits = inspect_pipe_edge_limits(
                    data, records, data[pipe_record.body:pipe_record.end], pipe, features,
                    name, members, body_identifier_summary, source_evidence=source, incidence_evidence=incidence)
                pipe_limit_summary["decoded"].append(limits)
                pipe["pipe_edge_limits"] = limits
                source["edge_limit_evidence"] = limits
                source.update(distance_two_fraction=limits["distance_two_fraction"],
                              distance_two_available=limits["distance_two_available"],
                              distance_two_status="Observed availability and active fraction from independently resolved single source-edge closure; resulting partial geometry unresolved")
                if limits["auxiliary_source_vertex"] is not None:
                    source["auxiliary_point_selection"]["source_vertex_association"] = limits["auxiliary_source_vertex"]
            except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
                pipe_limit_summary["unresolved"].append({"feature_object_id": pipe["object_id"], "reason": str(error)})
        body_placement_summary = decode_body_placement(body_binding_summary, assembly_summary, asm_summary)
        if any(r.is_primary and r.class_guid == NATIVE_JOINT_GUID for r in records):
            label_joint_cache_placements(assembly_summary, body_placement_summary, features)
        resolved_selection_features = {s["feature_object_id"] for s in selection_summary["resolved"]}
        unresolved_selection_features = {s["feature_object_id"] for s in selection_summary["unresolved"]}
        modeling_summary["unresolved"] = [
            item for item in modeling_summary["unresolved"]
            if item["reason"] != "Referenced start/end geometry selection not decoded"
            or item["object_id"] not in resolved_selection_features-unresolved_selection_features]
        parameter_table_summary = decode_parameter_tables(data, records, parameters)
        expression_dependency_summary = derive_expression_dependencies(parameters, parameter_table_summary)
        text_literal_summary = derive_text_literal_dependencies(parameters, parameter_table_summary)
        text_literal_ids = {item["parameter_object_id"] for item in text_literal_summary["derived"]}
        expression_dependency_summary["derived"].extend(text_literal_summary["derived"])
        expression_dependency_summary["unresolved"] = [item for item in expression_dependency_summary["unresolved"]
                                                         if item["parameter_object_id"] not in text_literal_ids]
        if text_literal_ids:
            expression_dependency_summary["scope"] += "; "+text_literal_summary["scope"]
            expression_dependency_summary["limitations"] = [item.replace("comparisons, Text,", "comparisons, nonliteral Text,")
                                                            for item in expression_dependency_summary["limitations"]]
        streams.append({
            "member": name, "features": features, "unbound_parameters": unbound,
            "parameter_tables": parameter_table_summary,
            "derived_expression_dependencies": expression_dependency_summary,
            "rejected_parameters": rejected, "candidate_record_headers": len(records),
            "record_index": record_index,
            "feature_discovery": discovery_summary,
            "sketch_decoding": sketch_summary,
            "sketch_record_coverage": sketch_coverage_summary,
            "offset_details": offset_detail_summary,
            "sketch_projections": projection_summary,
            "face_boundary_projections": face_boundary_summary,
            "sketch_texts": sketch_text_summary,
            "sketch_pattern_details": sketch_pattern_summary,
            "sketch_curved_patterns": curved_pattern_summary,
            "sketch_pattern_coverage": pattern_coverage_summary,
            "dimension_controls": dimension_control_summary,
            "dimension_control_modes": dimension_mode_summary,
            "tangent_dimension_caches": tangent_cache_summary,
            "profile_decoding": profile_summary,
            "modeling_decoding": modeling_summary,
            "placement_decoding": placement_summary,
            "construction_decoding": construction_summary,
            "plane_definitions": plane_definition_summary,
            "path_planes": path_plane_summary,
            "construction_definitions": construction_definition_summary,
            "construction_modes": construction_mode_summary,
            "construction_vertex_points": construction_vertex_summary,
            "selection_decoding": selection_summary,
            "revolve_axes": revolve_axis_summary,
            "tool_decoding": tool_summary,
            "hole_point_sources": hole_point_summary,
            "hole_supports": hole_support_summary,
            "boundary_fill_results": boundary_result_summary,
            "boundary_fill_sculpt_provenance": boundary_sculpt_summary,
            "pipe_path_provenance": pipe_provenance_summary,
            "pipe_vertex_contexts": pipe_vertex_summary,
            "pipe_asm_recipe_tags": pipe_tag_summary,
            "pipe_recipe_incidence": pipe_incidence_summary,
            "pipe_edge_limits": pipe_limit_summary,
            "pattern_placements": pattern_placement_summary,
            "timeline_decoding": timeline_summary,
            "assembly_decoding": assembly_summary,
            "component_creations": component_creation_summary,
            "mirror_component_creations": mirror_creation_summary,
            "pin_provenance": pin_provenance_summary,
            "copy_paste_occurrences": copy_paste_summary,
            "joint_decoding": joint_summary,
            "dependency_decoding": dependency_summary,
            "body_blob_bindings": body_binding_summary,
            "body_asm_identifiers": body_identifier_summary,
            "historical_body_components": historical_component_summary,
            "selection_recipe_incidence": selection_recipe_incidence_summary,
            "fpm_selection_tracking": fpm_selection_tracking_summary,
            "fpm_context_line_caches": fpm_context_cache_summary,
            "body_properties": body_property_summary,
            "body_selections": body_selection_summary,
            "selection_context_recipes": selection_context_summary,
            "direct_body_features": direct_body_summary,
            "silhouette_splits": silhouette_summary,
            "silhouette_direction_sources": silhouette_direction_summary,
            "silhouette_line_contexts": silhouette_line_summary,
            "sketch_surface_constraints": surface_constraint_summary,
            "special_fillets": special_fillet_summary,
            "surface_extrudes": surface_extrude_summary,
            "body_mapping_variants": body_mapping_variant_summary,
            "recipe_reference_components": recipe_component_summary,
            "timeline_state_details": timeline_state_summary,
            "body_property_variants": body_property_variant_summary,
            "brep_edge_axes": brep_axis_summary,
            "text_literal_dependencies": text_literal_summary,
            "selection_context_variants": selection_context_variant_summary,
            "remaining_body_inputs": remaining_input_summary,
            "mirror_datum_outputs": mirror_datum_summary,
            "mirror_nested_occurrences": mirror_nested_summary,
            "scale_vertex_points": scale_vertex_summary,
            "body_tool_selections": body_tool_selection_summary,
            "tool_body_inputs": tool_body_summary,
            "recipe_decoding": recipe_summary,
            "body_placement": body_placement_summary,
        })
        for key, summary in (('mirror_datum_reflections', datum_reflection_summary),
                             ('circular_placement_evidence', circular_cache_summary)):
            if summary['decoded'] or summary['unresolved']:
                streams[-1][key] = summary
        if fpm_body_tracking_summary['associations'] or fpm_body_tracking_summary['coverage'] or fpm_body_tracking_summary['unresolved']:
            streams[-1]['fpm_body_tracking'] = fpm_body_tracking_summary
    return {
        "file": str(path), "status": "experimental partial decoder",
        "scope": "Observed layouts in Fusion 2705.1.30; unsupported records remain undecoded",
        "limitations": [
            "Version-8 MetaStream indexes validate record boundaries; field semantics remain inferred from a small corpus.",
            "Type codes are local to the document and not treated as universal feature identifiers.",
            "Sketch support covers observed points, lines, circular/elliptical arcs, ellipses, NURBS, basic constraints and dimensions.",
            "Profile membership is partial; no general trimmed-contour reconstruction, topology, sketch solver or native writer.",
            "Modeling tools expose observed settings; input topology and unobserved modes remain partial.",
            "Timeline/state layouts and local rigid assemblies are partial; no complete history regeneration or body reconstruction.",
        ],
        "streams": streams,
        "asm_decoding": asm_summary,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--zstd-library")
    args = parser.parse_args()
    print(json.dumps([decode_basics(p, args.zstd_library) for p in args.files], indent=2))
