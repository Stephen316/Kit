"""Composite/spline Pipe sources and partial BRep-edge recipe provenance.

Known sketch paths reuse the base Pipe control parser. Topological edge paths
retain recipe/body provenance with unknown geometry and closedness; no false
open-path assumption is passed into the base fraction-mapping logic.
"""

import argparse
import json
import math
from pathlib import Path
import struct

from decode_brep_recipes import decode_recipe
from decode_path_pattern_composites import resolve_path_pattern_composite_path
from decode_pipe import decode_pipe
from decode_sketch import numbers, reference, same
from decode_sweep_profiles import resolve_sweep_profiles


def inspect_pipe_edge_path(data, records, body, feature, features):
    """Frame the captured populated optional selector layout without closure claims."""
    if (feature["class_guid"] != "73615646-8752-4EE6-AD02-0B90804B7CD7" or len(body) < 94
            or body[:7] != bytes.fromhex("00010000000000")
            or struct.unpack_from("<I", body, 7)[0] != 4 or body[11:13] != b"\0\1"
            or body[68] != 1 or struct.unpack_from("<I", body, 90)[0] != 0):
        raise ValueError("Unobserved partial BRep Pipe feature layout")
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {key: values[0] for key, values in grouped.items() if len(values) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Partial BRep Pipe typed identity missing, ambiguous or wrong class")
        return record, data[record.body:record.end]

    path_id = reference(body, 79)
    path = resolve_sweep_profiles(data, records, path_id, feature["object_id"], features)
    if len(path) != 1 or path[0]["kind"] != "BRepEdgePath":
        raise ValueError("Partial Pipe source is not a single owned edge recipe")
    selected = path[0]
    selected.update(is_closed=None, path_is_opposed_to_entity=None,
                    geometry_status="Owned edge recipe and historical body provenance only; exact edge curve and closedness unresolved")
    auxiliary_id = reference(body, 68)
    _, auxiliary = typed(auxiliary_id, "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44")
    if (len(auxiliary) != 178 or auxiliary[:23] != b"\0"*23
            or struct.unpack_from("<I", auxiliary, 47)[0] != 1
            or struct.unpack_from("<I", auxiliary, 75)[0] != 1
            or reference(auxiliary, 167) != feature["object_id"]):
        raise ValueError("Unobserved partial Pipe auxiliary selection count/layout/owner")
    descriptor_id = reference(auxiliary, 79)
    _, descriptor = typed(descriptor_id, "5662F619-2281-4AD9-93DC-1FCFDA1062E7")
    if (len(descriptor) != 276 or descriptor[:4] != b"\0"*4
            or struct.unpack_from("<I", descriptor, 15)[0] != 1
            or reference(descriptor, 265) != feature["object_id"]):
        raise ValueError("Unobserved partial Pipe auxiliary topology descriptor layout/owner")
    recipe_id = reference(descriptor, 4)
    record, _ = typed(recipe_id, "7ACC2A03-0261-4879-A14A-A93D661A5BDC")
    vertex_recipe = decode_recipe(data, record, primary)
    if vertex_recipe["payload_kind"] != "vertex_recipe_data":
        raise ValueError("Partial Pipe auxiliary source is not a vertex recipe")
    # Bindings are already independently decoded by the parameter pass. Preserve
    # their native roles without assigning the API distanceOne/distanceTwo map.
    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}
    controls = {}
    for offset, role in ((13, "AgainstDistance"), (24, "AlongDistance"), (46, "SectionSize"), (57, "SectionThickness")):
        identity = reference(body, offset)
        item = bindings.get(identity)
        if item is None or item["role"] != role or not math.isfinite(item["raw_float64"]):
            raise ValueError("Partial Pipe native parameter role/reference mismatch")
        controls[role] = {"binding_object_id": identity, "stored_value": item["raw_float64"]}
    return {"feature_object_id": feature["object_id"], "feature_class_guid": feature["class_guid"],
            "path_decode_status": "PartialBRepRecipeProvenance", "path": selected,
            "tool_settings_status": "Unresolved; this separate provenance summary does not supply full Pipe settings",
            "source_descriptor_class_guid": "5662F619-2281-4AD9-93DC-1FCFDA1062E7",
            "source_recipe_class_guid": "7ACC2A03-0261-4879-A14A-A93D661A5BDC",
            "stored_operation_code": 4, "stored_section_type_code": 0, "stored_hollow_flag": 0,
            "native_parameter_controls": controls,
            "distance_one_fraction": None, "distance_two_fraction": None,
            "fraction_scope": "API fraction mapping withheld because the native source edge closedness/geometry is unresolved",
            "auxiliary_point_selection": {"selection_record_object_id": auxiliary_id,
                                          "selection_class_guid": "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44",
                                          "stored_method_code": 1, "stored_xyz_cm": numbers(auxiliary, 23, 3),
                                          "descriptor_object_id": descriptor_id, "recipe_object_id": recipe_id,
                                          "vertex_recipe": vertex_recipe, "payload_hex": auxiliary.hex(),
                                          "role_scope": "Populated optional point-like selection with owned vertex recipe; exact Pipe role and selected topology remain unverified"},
            "input_selection_status": "Explicit owned edge recipe and historical native body anchor recovered",
            "geometry_status": "Partial source provenance only; closedness, persistent ASM edge/vertex identity, source curve and Pipe regeneration unresolved"}


def decode_pipe_paths(data, records, body, feature, features):
    """Full Pipe settings for validated sketch paths; edge provenance is separate."""
    if len(body) > 68 and body[68] == 1:
        raise ValueError("Populated Pipe selector layout requires separate provenance inspection; native edge closedness/fraction mapping unresolved")
    result = decode_pipe(data, records, body, feature, features, path_resolver=resolve_path_pattern_composite_path)
    if any(not math.isfinite(result[key]) for key in ("section_size_cm", "stored_section_thickness_cm", "native_against_fraction", "native_along_fraction")):
        raise ValueError("Nonfinite Pipe path control value")
    result.update(path_decode_status="DecodedSketchSourceGeometry",
                  fraction_scope="Observed open same-sketch composite Line/Arc or fitted-spline path; native fraction copies agree and API distanceOne is contrasted",
                  input_selection_status="Owned ordered descriptor/leaf sketch IDs and curve tags resolve natural source geometry",
                  geometry_status="Natural source curves and Pipe controls only; Path opposed flags, trimmed result geometry and Pipe regeneration unresolved")
    return result


def validate_fixtures(root, zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    folder = root/"pipepaths-3d11bd427946"
    truth = json.loads((folder/"ground_truth.json").read_text())
    assert (folder/"complete.txt").is_file() and not truth["errors"] and len(truth["samples"]) == 4
    report = {"api_version": truth["fusion_version"], "samples": [], "negative_checks": [],
              "interface": "decode_pipe_paths(data,records,body,feature,features) returns full sketch-source controls only; inspect_pipe_edge_path(data,records,body,feature,features) returns separate partial provenance and must not populate tool_settings",
              "validation_command": "python3 decode_pipe_paths.py --validate --zstd-library <local libzstd path>"}
    for sample in truth["samples"]:
        assert not sample["getter_errors"]
        archive = folder/sample["file"]
        main = decode_basics(archive, zstd_library)
        stream = next(s for s in main["streams"] if any(f["kind"] == "Pipe" for f in s["features"]))
        features = stream["features"]
        feature = next(f for f in features if f["kind"] == "Pipe")
        members = read_members(archive, zstd_library)
        data = members[stream["member"]]
        records, _ = design_records(data, members.get(stream["member"].replace("BulkStream.dat", "MetaStream.dat")))
        record = next(r for r in records if r.is_primary and r.object_id == feature["object_id"])
        body = data[record.body:record.end]
        partial = len(body) > 68 and body[68] == 1
        settings = (inspect_pipe_edge_path if partial else decode_pipe_paths)(data, records, body, feature, features)
        api = sample["settings"]
        selected = settings["path"]
        if settings["path_decode_status"] == "PartialBRepRecipeProvenance":
            try:
                decode_pipe_paths(data, records, body, feature, features)
            except ValueError as error:
                report["negative_checks"].append({"check": "Partial edge provenance cannot become full Pipe settings", "passed": True, "reason": str(error)})
            else:
                raise AssertionError("Partial edge provenance accepted as full settings")
            properties = {b["object_id"]: b for b in stream["body_properties"]["bodies"]}
            checks = {"api_actual_source_is_BRepEdge": len(api["path"]["members"]) == 1 and api["path"]["members"][0]["source"]["entity_type"] == "adsk::fusion::BRepEdge",
                      "owned_historical_body_name_matches_api_source_body": properties[selected["native_body_object_id"]]["name"] == api["path"]["members"][0]["source"]["body_name"],
                      "bounded_recipe_kind_is_edge": selected["recipe"]["payload_kind"] == "edge_recipe_data",
                      "auxiliary_owned_recipe_kind_is_vertex": settings["auxiliary_point_selection"]["vertex_recipe"]["payload_kind"] == "vertex_recipe_data",
                      "closure_and_fraction_mapping_remain_unresolved": selected["is_closed"] is None and settings["distance_one_fraction"] is None and settings["distance_two_fraction"] is None}
            edge_case = data, records, features, feature, record, settings
        else:
            checks = {"actual_section_and_hollow_flags_match": settings["stored_section_type_code"] == api["section_type"] and settings["is_hollow"] == api["is_hollow"],
                      "actual_section_size_matches": same([settings["section_size_cm"]], [api["section_size_cm"]]),
                      "actual_stored_thickness_matches": same([settings["stored_section_thickness_cm"]], [api["section_thickness_cm"]]),
                      "actual_open_path_fractions_match": same([settings["distance_one_fraction"]], [api["distance_one"]]) and settings["distance_two_fraction"] == api["distance_two"] is None,
                      "native_source_order_matches_actual_api": [m["kind"] for m in selected["members"]] == [m["source"]["entity_type"].split("::")[-1].removeprefix("Sketch") for m in api["path"]["members"]],
                      "native_open_source_agrees_with_api": selected["is_closed"] is False and api["path"]["is_closed"] is False,
                      "opposed_flags_not_inferred": all(m["path_is_opposed_to_entity"] is None for m in selected["members"])}
            for member, actual in zip(selected["members"], api["path"]["members"]):
                natural, geometry = member["natural_component_geometry"], actual["source"]["natural_world_geometry"]
                checks[member["kind"]+"_five_source_points_match_api"] = all(same(a["point_component_cm"], b["point_cm"]) for a, b in zip(natural["analytic_samples"], geometry["samples"]))
                checks[member["kind"]+"_five_derivatives_match_api"] = all(same(a["parameter_derivative_component"], b["tangent"]) for a, b in zip(natural["analytic_samples"], geometry["samples"]))
            sketch_case = data, records, features, feature, settings
        assert all(checks.values()), (sample["file"], checks)
        report["samples"].append({"archive": str(archive.relative_to(root)), "checks": checks,
                                   "status": "PartialProvenance" if partial else "DecodedSettings",
                                   ("partial_provenance" if partial else "decoded_settings"): settings, "actual_api_settings": api,
                                   "scope": "Actual API opposed flags and BRep curve/closedness are evidence only; unresolved native fields are not filled from API truth"})
    data, records, features, feature, settings = sketch_case
    first = settings["path"]["members"][0]
    for label, identity, offset, replacement in (("Sketch path descriptor owner mismatch", first["descriptor_object_id"], 253, struct.pack("<Q", settings["path"]["sketch_object_id"])),
                                                ("Sketch curve leaf tag missing", first["terminal_object_id"], 18, struct.pack("<Q", 999999))):
        record = next(r for r in records if r.is_primary and r.object_id == identity)
        changed = bytearray(data)
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        try:
            resolve_path_pattern_composite_path(bytes(changed), records, settings["path"]["selection_record_object_id"], feature["object_id"], features)
        except ValueError as error:
            report["negative_checks"].append({"check": label, "passed": True, "reason": str(error)})
        else:
            raise AssertionError(label)
    data, records, features, feature, feature_record, settings = edge_case
    descriptor_id = settings["path"]["descriptor_object_id"]
    descriptor = next(r for r in records if r.is_primary and r.object_id == descriptor_id)
    auxiliary = next(r for r in records if r.is_primary and r.object_id == settings["auxiliary_point_selection"]["selection_record_object_id"])
    recipe = next(r for r in records if r.is_primary and r.object_id == settings["path"]["recipe"]["object_id"])
    marker = data.index(b"edge_recipe_data", recipe.body, recipe.end)
    for label, offset, replacement in (("Edge descriptor owner mismatch", descriptor.end-10, struct.pack("<Q", settings["path"]["native_body_object_id"])),
                                        ("Auxiliary point selector owner mismatch", auxiliary.end-10, struct.pack("<Q", settings["path"]["native_body_object_id"])),
                                        ("Wrong source recipe kind", marker, b"xxxx_recipe_data")):
        changed = bytearray(data)
        changed[offset:offset+len(replacement)] = replacement
        try:
            inspect_pipe_edge_path(bytes(changed), records, data[feature_record.body:feature_record.end], feature, features)
        except ValueError as error:
            report["negative_checks"].append({"check": label, "passed": True, "reason": str(error)})
        else:
            raise AssertionError(label)
    report["coverage"] = {"decoded_sketch_settings": 3, "separate_partial_brep_provenance": 1}
    report["limitations"] = ["Three sketch-source Pipe fixtures provide full control/source decoding; the BRep-edge fixture provides separate partial owned recipe/body provenance only and remains unsupported by the full settings decoder.",
                              "BRep path closedness and exact geometric edge remain unresolved, so API fraction mapping is withheld. The optional point-like selector is preserved without assigning an exact Pipe role.",
                              "Path opposed flags, per-result topology and geometry regeneration are not decoded. API truth is never injected into unknown native fields.",
                              "All generated operations are NewBody in the root component; other Pipe operations, occurrence contexts and assembly/joint transforms remain outside this stage."]
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", required=True)
    parser.add_argument("--zstd-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("pipe-path-decoding.json"))
    args = parser.parse_args()
    report = validate_fixtures(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"samples": len(report["samples"]), "negative_checks": len(report["negative_checks"]), "output": str(args.output)}))
