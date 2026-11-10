"""Explicit single SketchArc Loft guides, with component-space analytic samples.

The curve already exists in decoded sketch geometry. This module resolves its
owned descriptor/leaf identity and preserves native orientation; it does not
derive guide traversal direction from section order or regenerate Loft bodies.
"""

import argparse
import copy
import json
import math
from pathlib import Path
import struct

from decode_loft_modes import decode_loft_modes
from decode_placement import cross, rigid_matrix, transform_point, transform_vector
from decode_selection import native_proxy_references, resolve_single_sketch_curve
from decode_sketch import reference, same


def resolve_loft_guide(data, records, selection_id, owner_id, features):
    """Five-argument guide_resolver hook; existing Line selections stay unchanged."""
    selected = resolve_single_sketch_curve(data, records, selection_id, owner_id, features, ("Line", "Arc"))
    if selected["kind"] == "Line":
        return selected

    def unique(identity, guid):
        candidates = [r for r in records if r.is_primary and r.object_id == identity]
        if len(candidates) != 1 or candidates[0].class_guid != guid:
            raise ValueError("Curved Loft guide typed identity missing, ambiguous or wrong class")
        return candidates[0]

    proxy = unique(selection_id, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
    descriptors, props = native_proxy_references(data, proxy)
    if props or descriptors != [selected["descriptor_object_id"]]:
        raise ValueError("Unobserved curved Loft proxy attributes or descriptor list")
    descriptor = unique(selected["descriptor_object_id"], "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
    payload = data[descriptor.body:descriptor.end]
    if (len(payload) != 263 or struct.unpack_from("<I", payload, 13)[0] != 1
            or reference(payload, 252) != owner_id):
        raise ValueError("Curved Loft descriptor count/owner mismatch")
    unique(selected["terminal_object_id"], "E2CEFD18-D755-4E09-8E7F-953A2F6D43F8")
    unique(selected["curve_object_id"], "F0130424-8B7E-4092-93C9-1CA807482534")
    sketches = [f for f in features if f["kind"] == "Sketch" and f["sketch_object_id"] == selected["sketch_object_id"]]
    if len(sketches) != 1 or "placement" not in sketches[0]:
        raise ValueError("Curved Loft guide sketch placement unresolved or ambiguous")
    sketch = sketches[0]
    curves = [c for c in sketch.get("geometry", []) if c["object_id"] == selected["curve_object_id"]
              and c.get("entity_tag") == selected["curve_entity_tag"] and c["kind"] == "Arc"]
    if len(curves) != 1:
        raise ValueError("Curved Loft guide source curve unresolved or ambiguous")
    curve = curves[0]
    matrix = rigid_matrix(sketch["placement"]["sketch_to_component_matrix"])
    radius, start, end = curve["radius_cm"], curve["start_angle_radians"], curve["end_angle_radians"]
    if (not all(math.isfinite(x) for x in (radius, start, end)) or radius <= 0
            or not 0 < end-start < 2*math.pi):
        raise ValueError("Curved Loft guide is not an observed bounded positive-sweep open arc")
    center = transform_point(matrix, curve["center_cm"])
    normal = transform_vector(matrix, curve["normal"])
    axis = transform_vector(matrix, curve["reference_axis"])
    if not same([sum(x*x for x in normal), sum(x*x for x in axis), sum(x*y for x, y in zip(normal, axis))], [1, 1, 0]):
        raise ValueError("Curved Loft guide angular axes are not orthonormal")
    transverse = cross(normal, axis)
    samples = []
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        angle = start+fraction*(end-start)
        point = [c+radius*(math.cos(angle)*a+math.sin(angle)*b) for c, a, b in zip(center, axis, transverse)]
        derivative = [radius*(-math.sin(angle)*a+math.cos(angle)*b) for a, b in zip(axis, transverse)]
        samples.append({"parameter_fraction": fraction, "parameter_radians": angle,
                        "point_component_cm": point, "parameter_derivative_component_cm_per_radian": derivative})
    native_start, native_end = (transform_point(matrix, curve[key]) for key in ("start_cm", "end_cm"))
    if not same(native_start, samples[0]["point_component_cm"]) or not same(native_end, samples[-1]["point_component_cm"]):
        raise ValueError("Curved Loft guide copied endpoints disagree with angular geometry")
    selected.update(sketch_name=sketch.get("name"), component_geometry={
        "kind": "Arc", "center_cm": center, "radius_cm": radius, "normal": normal, "reference_axis": axis,
        "start_cm": native_start, "end_cm": native_end, "start_angle_radians": start, "end_angle_radians": end,
        "length_cm": radius*(end-start), "analytic_samples": samples},
        geometry_source="Existing bounded sketch Arc parameters and rigid sketch-to-component placement",
        orientation_scope="Native sketch arc start/end and positive angular sweep; API guide traversal relative to section order is not inferred",
        coordinate_scope="Parent component coordinates; no assembly occurrence or joint transformations applied",
        derivative_scope="Analytic angular derivatives; captured API getTangent vectors match these radius-scaled vectors, with no unit-vector assumption")
    return selected


def decode_loft_curved_guides(data, records, body, feature, features):
    """Observed open solid two-profile Free-end NewBody Loft with one Arc guide."""
    result = decode_loft_modes(data, records, body, feature, features, guide_resolver=resolve_loft_guide)
    if (result["operation"] != "NewBody" or result["is_closed"] or not result["is_solid"]
            or result["section_count"] != 2 or len(result["sections"]) != 2
            or any("profile" not in section for section in result["sections"])
            or any((result.get(side+"_condition") or {}).get("type") != "Free" for side in ("start", "end"))
            or result["guide_count"] != 1):
        raise ValueError("Curved Loft wrapper requires an open solid NewBody with two profile sections, Free ends and exactly one guide")
    if result["is_centerline"]:
        guide = result["centerline"]
        if result["rails"]:
            raise ValueError("Curved Loft centerline/rail combination is unverified")
    else:
        if result["centerline"] is not None or len(result["rails"]) != 1:
            raise ValueError("Curved Loft wrapper requires exactly one rail when no centerline is present")
        guide = result["rails"][0]["selection"]
    if guide.get("kind") != "Arc":
        raise ValueError("Curved Loft wrapper requires one circular SketchArc guide")
    result["guide_status"] = "Explicit single circular-arc sketch centerline or rail with native arc geometry; only open solid two-profile NewBody lofts with Free ends are contrasted"
    return result


def validate_fixtures(root, zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    folder = root/"loftcurvedguides-79a1266af54e"
    truth = json.loads((folder/"ground_truth.json").read_text())
    assert (folder/"complete.txt").is_file() and len(truth["samples"]) == 2 and not truth["errors"]
    report = {"api_version": truth["fusion_version"], "samples": [], "negative_checks": [],
              "interface": "resolve_loft_guide(data, records, selection_id, owner_id, features), five-argument guide_resolver callback; decode_loft_curved_guides provides the observed NewBody wrapper",
              "integration": "decode_loft_modes(..., guide_resolver=resolve_loft_guide); retain default strict Line resolver when callback absent",
              "validation_command": "python3 decode_loft_curved_guides.py --validate --zstd-library <local libzstd path>"}
    for sample in truth["samples"]:
        archive = folder/sample["file"]
        decoded = decode_basics(archive, zstd_library)
        stream = next(s for s in decoded["streams"] if any(f["kind"] == "Loft" for f in s["features"]))
        features = stream["features"]
        feature = next(f for f in features if f["kind"] == "Loft")
        members = read_members(archive, zstd_library)
        data = members[stream["member"]]
        records, _ = design_records(data, members.get(stream["member"].replace("BulkStream.dat", "MetaStream.dat")))
        record = next(r for r in records if r.is_primary and r.object_id == feature["object_id"])
        settings = decode_loft_curved_guides(data, records, data[record.body:record.end], feature, features)
        selected = settings["centerline"] if settings["is_centerline"] else settings["rails"][0]["selection"]
        geometry = selected["component_geometry"]
        actual = sample["guides"][0]["arc"]
        getter = sample["settings"]
        checks = {"guide_entity_is_actual_SketchArc": sample["guides"][0]["entity_type"] == "adsk::fusion::SketchArc" and selected["kind"] == "Arc",
                  "loft_controls_match_api": all(settings[k] == getter[k] for k in ("is_solid", "is_closed", "is_tangent_edges_merged", "section_count", "guide_count", "is_centerline")),
                  "arc_center_radius_normal_and_axis_match_api": same(geometry["center_cm"], actual["center_world_cm"]) and same([geometry["radius_cm"]], [actual["radius_cm"]]) and same(geometry["normal"], actual["normal_world"]) and same(geometry["reference_axis"], actual["reference_vector_world"]),
                  "native_start_end_match_actual_api_orientation": same(geometry["start_cm"], actual["start_world_cm"]) and same(geometry["end_cm"], actual["end_world_cm"]),
                  "actual_api_reverses_requested_creation_endpoints": same(geometry["start_cm"], sample["requested_guide_three_points_world_cm"][-1]) and same(geometry["end_cm"], sample["requested_guide_three_points_world_cm"][0]),
                  "arc_angle_interval_and_length_match_api": same([geometry["start_angle_radians"], geometry["end_angle_radians"], geometry["length_cm"]], [actual["start_angle_radians"], actual["end_angle_radians"], actual["evaluator"]["length_cm"]]),
                  "all_five_analytic_points_match_actual_api_evaluator": all(same(a["point_component_cm"], b["point_world_cm"]) for a, b in zip(geometry["analytic_samples"], actual["evaluator"]["samples"])),
                  "all_five_angular_derivatives_match_actual_api_getTangent_vectors": all(same(a["parameter_derivative_component_cm_per_radian"], b["tangent_world"]) for a, b in zip(geometry["analytic_samples"], actual["evaluator"]["samples"]))}
        assert all(checks.values()), (sample["file"], checks)
        report["samples"].append({"archive": str(archive.relative_to(root)), "checks": checks,
                                   "decoded_loft_settings": settings, "actual_api_guides": sample["guides"],
                                   "section_api_geometry": sample["sections"],
                                   "scope": "API world/component agreement applies to these root-component fixtures only"})
        baseline = (data, records, features, selected, feature, record, settings)
    data, records, features, selected, feature, feature_record, settings = baseline
    for label, target, delta, packed in (("Descriptor owner mismatch rejected", selected["descriptor_object_id"], 253, struct.pack("<Q", selected["sketch_object_id"])),
                                          ("Descriptor count mismatch rejected", selected["descriptor_object_id"], 13, struct.pack("<I", 2)),
                                          ("Leaf curve tag mismatch rejected", selected["terminal_object_id"], 18, struct.pack("<Q", 999999)),
                                          ("Proxy owner mismatch rejected", selected["selection_record_object_id"], -10, struct.pack("<Q", selected["sketch_object_id"]))):
        record = next(r for r in records if r.is_primary and r.object_id == target)
        offset = record.body+delta if delta >= 0 else record.end+delta
        corrupted = bytearray(data)
        corrupted[offset:offset+len(packed)] = packed
        try:
            resolve_loft_guide(bytes(corrupted), records, selected["selection_record_object_id"], feature["object_id"], features)
        except ValueError as error:
            report["negative_checks"].append({"check": label, "passed": True, "reason": str(error)})
        else:
            raise AssertionError(label)
    modified = copy.deepcopy(features)
    sketch = next(f for f in modified if f["kind"] == "Sketch" and f["sketch_object_id"] == selected["sketch_object_id"])
    del sketch["placement"]
    try:
        resolve_loft_guide(data, records, selected["selection_record_object_id"], feature["object_id"], modified)
    except ValueError as error:
        report["negative_checks"].append({"check": "Missing sketch placement rejected", "passed": True, "reason": str(error)})
    else:
        raise AssertionError("Missing sketch placement accepted")
    surface_body = bytearray(data[feature_record.body:feature_record.end])
    surface_body[settings["closure_field_relative_offset"]+1] = 0
    try:
        decode_loft_curved_guides(data, records, bytes(surface_body), feature, features)
    except ValueError as error:
        assert "requires an open solid NewBody" in str(error)
        report["negative_checks"].append({"check": "Uncaptured surface curved-guide combination rejected", "passed": True, "reason": str(error)})
    else:
        raise AssertionError("Uncaptured surface curved guide accepted")
    report["limitations"] = ["One circular SketchArc guide per captured loft; composite guides, BRep edges, NURBS and curved-guide combinations remain unverified.",
                              "Native orientation is preserved even when opposite to requested creation points or section order; no traversal reversal flag is inferred.",
                              "Output geometry is in parent component coordinates, with no assembly/joint solving or general world-coordinate claim.",
                              "Analytic evaluator samples describe the existing input curve; they do not regenerate Loft surfaces, trims or result bodies.",
                              "The wrapper requires open solid NewBody, exactly two profile sections with Free ends, and exactly one Arc centerline or rail. Other combinations are rejected; the reusable resolver's Line delegation does not expand wrapper acceptance."]
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", required=True)
    parser.add_argument("--zstd-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("loft-curved-guide-decoding.json"))
    args = parser.parse_args()
    report = validate_fixtures(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"samples": len(report["samples"]), "negative_checks": len(report["negative_checks"]), "output": str(args.output)}))
