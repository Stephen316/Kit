"""Observed body PathPattern controls with composite/spline source selections.

Reuses the existing strict controller parser and natural sketch-curve evaluator.
Path traversal, opposed flags and per-instance geometry are not reconstructed.
"""

import argparse
import copy
import json
import math
from pathlib import Path
import struct

from decode_body_selections import decode_body_selections
from decode_loft_composite_guides import _source_geometry
from decode_path_patterns import decode_path_pattern
from decode_selection import native_proxy_references
from decode_sketch import reference, same


def resolve_path_pattern_composite_path(data, records, selection_id, owner_id, features):
    """Resolve observed same-sketch Line/Arc or open FittedSpline descriptor lists."""
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {key: values[0] for key, values in grouped.items() if len(values) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Composite PathPattern typed reference missing, ambiguous or wrong class")
        return record, data[record.body:record.end]

    proxy, payload = typed(selection_id, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
    descriptors, props = native_proxy_references(data, proxy)
    if (props or len(descriptors) not in (1, 2) or len(set(descriptors)) != len(descriptors)
            or reference(payload, len(payload)-11) != owner_id or payload[:2] != b"\0\0"):
        raise ValueError("Unobserved composite PathPattern proxy count/attributes/owner")
    offset = 6+11*len(descriptors)
    if payload[offset:offset+6] != b"\0\0\1\0\0\0":
        raise ValueError("Unobserved composite PathPattern secondary list")
    flags_id = reference(payload, offset+6)
    _, flags = typed(flags_id, "2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B")
    if flags != bytes.fromhex("0000010100"):
        raise ValueError("Unobserved composite PathPattern secondary flags")
    classes = {"Line": "DCA267ED-D615-4934-B64F-AD805E8003E2", "Arc": "F0130424-8B7E-4092-93C9-1CA807482534",
               "FittedSpline": "D82E012F-6DDD-4AED-BDE1-C0F7F9100B9B"}
    members = []
    for index, identity in enumerate(descriptors):
        _, descriptor = typed(identity, "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
        if (len(descriptor) != 263 or descriptor[:2] != b"\0\0"
                or struct.unpack_from("<I", descriptor, 13)[0] != 1 or reference(descriptor, 252) != owner_id):
            raise ValueError("Composite PathPattern descriptor count/layout/owner mismatch")
        leaf_id = reference(descriptor, 2)
        _, leaf = typed(leaf_id, "E2CEFD18-D755-4E09-8E7F-953A2F6D43F8")
        if len(leaf) != 26 or leaf[:10] != b"\0"*10:
            raise ValueError("Unsupported composite PathPattern sketch-curve leaf")
        sketch_id, tag = struct.unpack_from("<QQ", leaf, 10)
        sketches = [f for f in features if f["kind"] == "Sketch" and f["sketch_object_id"] == sketch_id]
        matches = [(sketch, curve) for sketch in sketches for curve in sketch.get("geometry", [])
                   if curve.get("entity_tag") == tag and curve["kind"] in classes]
        if len(sketches) != 1 or len(matches) != 1:
            raise ValueError("Composite PathPattern source sketch/tag missing, unsupported or ambiguous")
        sketch, curve = matches[0]
        typed(curve["object_id"], classes[curve["kind"]])
        members.append({"index": index, "descriptor_object_id": identity, "terminal_object_id": leaf_id,
                        "sketch_object_id": sketch_id, "sketch_name": sketch.get("name"),
                        "curve_object_id": curve["object_id"], "curve_entity_tag": tag, "kind": curve["kind"],
                        "natural_component_geometry": _source_geometry(sketch, curve), "path_is_opposed_to_entity": None})
    if len({member["sketch_object_id"] for member in members}) != 1:
        raise ValueError("Cross-sketch composite PathPattern paths remain unverified")
    kinds = [member["kind"] for member in members]
    if kinds == ["Line", "Arc"]:
        line, arc = [member["natural_component_geometry"] for member in members]
        if not same(line["end_cm"], arc["start_cm"]) or same(line["start_cm"], arc["end_cm"]):
            raise ValueError("Unobserved composite PathPattern endpoint connection")
        first = line["analytic_samples"][-1]["parameter_derivative_component"]
        second = arc["analytic_samples"][0]["parameter_derivative_component"]
        lengths = [math.sqrt(sum(x*x for x in vector)) for vector in (first, second)]
        if not same([x/lengths[0] for x in first], [x/lengths[1] for x in second]):
            raise ValueError("Nontangent Line/Arc PathPattern remains unverified")
        kind = "CompositeSketchPath"
    elif kinds == ["FittedSpline"]:
        kind = "FittedSplinePath"
    else:
        raise ValueError("Only observed ordered Line/Arc or single fitted-spline paths supported")
    return {"kind": kind, "selection_record_object_id": selection_id, "sketch_object_id": members[0]["sketch_object_id"],
            "sketch_name": members[0]["sketch_name"], "member_count": len(members), "members": members,
            "is_closed": False, "closure_scope": "Observed source endpoints differ; no general native Path closure bit claimed",
            "secondary_flags_record_object_id": flags_id, "secondary_flags_hex": flags.hex(),
            "order_scope": "Explicit counted native descriptor order; actual API source member order agrees in captures",
            "traversal_scope": "Natural source geometry only; opposed/traversal flags unresolved and not inferred from connectivity",
            "coordinate_scope": "Parent component coordinates; no occurrence/joint transforms or instance placement regeneration"}


def decode_path_pattern_composites(data, records, body, feature, features):
    result = decode_path_pattern(data, records, body, feature, features, path_resolver=resolve_path_pattern_composite_path)
    if (result["is_flipped"] or result["is_symmetric"] or result["stored_start_fraction"] != 0
            or result["suppressed_element_ids"] or not math.isfinite(result["distance_cm"])):
        raise ValueError("Composite PathPattern flip/symmetry/nonzero start/suppression variants remain unverified")
    selected = result["path"]
    if selected["kind"] == "FittedSplinePath" and not result["orientation_along_path"]:
        raise ValueError("Identical-orientation fitted-spline PathPattern remains unverified")
    descriptors = [item["descriptor_object_id"] for item in result["input_descriptors"]]
    if result["auxiliary_descriptor_object_ids"] != descriptors:
        raise ValueError("Composite PathPattern input proxy/collection descriptor copies disagree")
    body_summary = decode_body_selections(data, records)
    body_map = {item["object_id"]: item for item in body_summary["body_descriptors"]}
    for item in result["input_descriptors"]:
        descriptor = body_map.get(item["descriptor_object_id"])
        if descriptor is None or descriptor["owner_object_id"] != feature["object_id"] or descriptor["context_record_object_ids"]:
            raise ValueError("Composite PathPattern native input body identity/owner/context unresolved")
        item.update(native_body_object_id=descriptor["native_body_object_id"], body_anchor_object_id=descriptor["body_anchor_object_id"],
                    source_owner_object_id=descriptor["source_owner_object_id"])
    anchors = {item["object_id"]: item for item in body_summary["body_anchors"]}
    if any(identity not in anchors or anchors[identity]["source_owner_object_id"] != feature["object_id"]
           for identity in result["result_record_object_ids"]):
        raise ValueError("Composite PathPattern result anchor ownership unresolved")
    result.update(pattern_entity_type="Bodies", native_input_body_object_ids=[item["native_body_object_id"] for item in result["input_descriptors"]],
                  start_fraction_scope="Observed zero start, unflipped and nonsymmetric composite/spline cases only",
                  input_selection_status="Explicit proxy/collection descriptor copies and owned typed body anchors select native historical input identities",
                  compute_status="Body input type proven by native body descriptors; invariant controller words retained by base reader without assigning new compute semantics",
                  geometry_status="Natural path source geometry and controls decoded; opposed flags, per-instance transforms and body regeneration remain unresolved")
    return result


def validate_fixtures(root, zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    folder = root/"pathpatterncomposites-b6b4cf615504"
    truth = json.loads((folder/"ground_truth.json").read_text())
    assert (folder/"complete.txt").is_file() and not truth["errors"] and len(truth["samples"]) == 4
    report = {"api_version": truth["fusion_version"], "samples": [], "negative_checks": [],
              "interface": "decode_path_pattern_composites(data,records,body,feature,features); uses existing decode_path_pattern(..., path_resolver=...) hook",
              "validation_command": "python3 decode_path_pattern_composites.py --validate --zstd-library <local libzstd path>"}
    for sample in truth["samples"]:
        assert not sample["getter_errors"]
        archive = folder/sample["file"]
        main = decode_basics(archive, zstd_library)
        stream = next(s for s in main["streams"] if any(f["kind"] == "PathPattern" for f in s["features"]))
        features = stream["features"]
        feature = next(f for f in features if f["kind"] == "PathPattern")
        members = read_members(archive, zstd_library)
        data = members[stream["member"]]
        records, _ = design_records(data, members.get(stream["member"].replace("BulkStream.dat", "MetaStream.dat")))
        record = next(r for r in records if r.is_primary and r.object_id == feature["object_id"])
        settings = decode_path_pattern_composites(data, records, data[record.body:record.end], feature, features)
        api = sample["settings"]
        selected = settings["path"]
        properties = {item["object_id"]: item for item in stream["body_properties"]["bodies"]}
        checks = {"quantity_distance_orientation_flags_match_actual_api": all(settings[k] == api[k] for k in ("quantity", "distance_cm", "start_fraction", "is_flipped", "is_symmetric", "orientation_along_path", "suppressed_element_ids")),
                  "distance_type_matches_actual_api": settings["distance_type"] == {0: "Extent", 1: "Spacing"}[api["distance_type"]],
                  "input_counts_and_body_type_match_actual_api": settings["input_body_count"] == api["input_count"] and api["pattern_entity_type"] == 2 and all(i["entity_type"] == "adsk::fusion::BRepBody" for i in api["inputs"]),
                  "explicit_native_input_body_names_match_api": [properties[i]["name"] for i in settings["native_input_body_object_ids"]] == [i["name"] for i in api["inputs"]],
                  "generated_reference_count_plus_seed_count_matches_api_body_count": settings["generated_result_reference_count"]+settings["input_body_count"] == api["result_body_count"],
                  "native_member_order_matches_api_source_kinds": [m["kind"] for m in selected["members"]] == [m["source"]["entity_type"].split("::")[-1].removeprefix("Sketch") for m in api["path"]["members"]],
                  "decoded_opposed_flags_stay_unresolved": all(m["path_is_opposed_to_entity"] is None for m in selected["members"])}
        for member, actual in zip(selected["members"], api["path"]["members"]):
            natural, actual_geometry = member["natural_component_geometry"], actual["source"]["natural_world_geometry"]
            checks[member["kind"]+"_five_source_points_match_api"] = all(same(a["point_component_cm"], b["point_cm"]) for a, b in zip(natural["analytic_samples"], actual_geometry["samples"]))
            checks[member["kind"]+"_five_derivatives_match_api"] = all(same(a["parameter_derivative_component"], b["tangent"]) for a, b in zip(natural["analytic_samples"], actual_geometry["samples"]))
            checks[member["kind"]+"_source_domain_matches_api"] = same(natural["parameter_domain"], actual_geometry["parameter_extents"])
        assert all(checks.values()), (sample["file"], checks)
        report["samples"].append({"archive": str(archive.relative_to(root)), "checks": checks,
                                   "decoded": settings, "actual_api_settings": api, "actual_api_pattern_elements": sample["pattern_elements"],
                                   "association_scope": "API Path opposed flags and element matrices retained only as evidence; no native traversal or result-body/element mapping asserted"})
        if selected["kind"] == "CompositeSketchPath":
            baseline = data, records, features, feature, record, settings
    data, records, features, feature, feature_record, settings = baseline
    selected = settings["path"]
    first = selected["members"][0]
    for label, identity, offset, replacement in (("Path descriptor owner mismatch", first["descriptor_object_id"], 253, struct.pack("<Q", selected["sketch_object_id"])),
                                                ("Path curve tag missing", first["terminal_object_id"], 18, struct.pack("<Q", 999999)),
                                                ("Unobserved secondary flags", selected["secondary_flags_record_object_id"], 2, b"\0")):
        record = next(r for r in records if r.is_primary and r.object_id == identity)
        changed = bytearray(data)
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        try:
            resolve_path_pattern_composite_path(bytes(changed), records, selected["selection_record_object_id"], feature["object_id"], features)
        except ValueError as error:
            report["negative_checks"].append({"check": label, "passed": True, "reason": str(error)})
        else:
            raise AssertionError(label)
    changed = bytearray(data)
    proxy = next(r for r in records if r.is_primary and r.object_id == selected["selection_record_object_id"])
    first_ref, second_ref = changed[proxy.body+6:proxy.body+17], changed[proxy.body+17:proxy.body+28]
    changed[proxy.body+6:proxy.body+17], changed[proxy.body+17:proxy.body+28] = second_ref, first_ref
    try:
        resolve_path_pattern_composite_path(bytes(changed), records, selected["selection_record_object_id"], feature["object_id"], features)
    except ValueError as error:
        report["negative_checks"].append({"check": "Unobserved Arc/Line descriptor order rejected", "passed": True, "reason": str(error)})
    else:
        raise AssertionError("Unobserved source order accepted")
    changed = bytearray(data)
    control = next(r for r in records if r.is_primary and r.object_id == settings["control_record_object_id"])
    struct.pack_into("<d", changed, control.body+105, 0.25)
    try:
        decode_path_pattern_composites(bytes(changed), records, data[feature_record.body:feature_record.end], feature, features)
    except ValueError as error:
        report["negative_checks"].append({"check": "Uncaptured nonzero start variant rejected", "passed": True, "reason": str(error)})
    else:
        raise AssertionError("Uncaptured nonzero start accepted")
    report["limitations"] = ["Only same-sketch tangent Line then Arc (line end equals natural arc start), or single open FittedSpline, is resolved in this new branch; old single-line/arc behavior remains with its original reader.",
                              "New branch requires zero start, no flip/symmetry/suppression, body inputs and positive finite distance. Spline identical orientation remains unverified; observed spline orientation is along path.",
                              "Path opposed/traversal flags, per-instance matrices, native/API element correspondence and persistent topology mapping remain unresolved. Matrices in the report are actual API evidence, not decoded native output.",
                              "Natural geometry evaluation reuses the existing source-curve evaluator, without Loft-specific orientation restrictions. Component coordinates are not general assembly/world coordinates."]
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", required=True)
    parser.add_argument("--zstd-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("path-pattern-composite-decoding.json"))
    args = parser.parse_args()
    report = validate_fixtures(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"samples": len(report["samples"]), "negative_checks": len(report["negative_checks"]), "output": str(args.output)}))
