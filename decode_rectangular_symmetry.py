"""Observed rectangular symmetry translation sets, without instance identities.

Only single-body positive-spacing patterns on explicit component X/Y axes have
symmetry getter contrasts. Native keys, API IDs and result bodies stay separate.
"""

import argparse
import copy
import json
import math
from pathlib import Path

from decode_sketch import same


SCOPE = "Observed symmetric single-body positive-spacing patterns on explicit component X/Y axes; analytic placement sets only, with no instance ID association or body-cache application"


def rectangular_symmetry_translation_set(settings):
    """Return the observed symmetric grid translation set after strict tool parsing.

    For a symmetric axis, logical index i uses spacing coefficient
    i-floor((quantity-1)/2). Odd quantities balance around the seed; even
    quantities leave one additional positive instance. This is a getter/cache
    validated formula, not a key/ordinal interpretation.
    """
    flags = [settings.get("symmetric_one"), settings.get("symmetric_two")]
    if any(type(flag) is not bool for flag in flags) or not any(flags):
        raise ValueError("Expected at least one explicit rectangular symmetry flag")
    if settings.get("pattern_entity_type") != "Bodies" or settings.get("input_count") != 1:
        raise ValueError("Symmetric placement contrasts cover single-body inputs only")
    if settings.get("distance_type") != "Spacing":
        raise ValueError("Symmetric extent placement getter contrast unavailable")
    quantities = [settings.get("quantity_one"), settings.get("quantity_two")]
    if any(type(q) is not int or q < 2 for q in quantities):
        raise ValueError("Symmetric placement contrasts require two active grid directions")
    containers = []
    for name, axis, direction in (("one", "X", [1, 0, 0]), ("two", "Y", [0, 1, 0])):
        distance = settings.get("distance_"+name+"_cm")
        if not isinstance(distance, (int, float)) or not math.isfinite(distance) or distance <= 0:
            raise ValueError("Symmetric zero/negative distance getter contrast unavailable")
        entity = (settings.get("direction_"+name+"_selection") or {}).get("entity", {})
        if (entity.get("kind") != "ConstructionAxis" or entity.get("name") != axis
                or not same(entity.get("origin_cm", []), [0, 0, 0])
                or not same(entity.get("direction", []), direction)
                or not same(settings.get("direction_"+name, []), direction)
                or entity.get("origin_container_object_id") is None):
            raise ValueError("Symmetric placement contrasts cover explicit native component X/Y axes only")
        containers.append(entity["origin_container_object_id"])
    if containers[0] != containers[1]:
        raise ValueError("Symmetric directions belong to different component origin containers")
    # Local import keeps the helper safe to import from the placement module.
    from decode_pattern_placements import rectangular_translation_set
    nonsymmetric = dict(settings, symmetric_one=False, symmetric_two=False)
    placements = rectangular_translation_set(nonsymmetric)
    center = [(q-1)//2 if flag else 0 for q, flag in zip(quantities, flags)]
    shift = [center[0]*settings["distance_one_cm"], center[1]*settings["distance_two_cm"], 0]
    for placement in placements:
        placement["signed_spacing_coefficients"] = [i-c for i, c in zip(placement["logical_grid_coordinates"], center)]
        placement["translation_cm"] = [v-s for v, s in zip(placement["translation_cm"], shift)]
        for offset, value in zip((3, 7, 11), placement["translation_cm"]):
            placement["matrix"][offset] = value
    return placements


def validate_fixtures(root, zstd_library):
    from decode_basics import decode_basics
    from decode_pattern_placements import _same_matrix_set
    from fusion_archive import read_members
    from fusion_metadata import design_records
    from decode_sketch import reference
    import struct

    folder = root/"rectsymmetry-f09c57dcfd51"
    truth = json.loads((folder/"ground_truth.json").read_text())
    assert (folder/"complete.txt").is_file() and not truth["errors"] and len(truth["samples"]) == 4
    report = {"scope": SCOPE, "api_version": truth["fusion_version"], "samples": [], "negative_checks": [],
              "interface": "rectangular_symmetry_translation_set(settings) -> placement list; raises ValueError outside observed scope; call after strict decode_rectangular_pattern_modes",
              "validation_command": "python3 decode_rectangular_symmetry.py --validate --zstd-library <local libzstd path>"}
    for sample in truth["samples"]:
        archive = folder/sample["file"]
        decoded = decode_basics(archive, zstd_library)
        stream = next(s for s in decoded["streams"] if any(f["kind"] == "RectangularPattern" for f in s["features"]))
        feature = next(f for f in stream["features"] if f["kind"] == "RectangularPattern")
        settings = feature["tool_settings"]
        before = copy.deepcopy(settings)
        placements = rectangular_symmetry_translation_set(settings)
        actual = [e["transform"] for e in sample["pattern_elements"]]
        members = read_members(archive, zstd_library)
        data = members[stream["member"]]
        records, _ = design_records(data, members.get(stream["member"].replace("BulkStream.dat", "MetaStream.dat")))
        native = []
        for identity, key in zip(settings["element_record_object_ids"], settings["stored_element_keys"]):
            candidates = [r for r in records if r.is_primary and r.object_id == identity]
            assert len(candidates) == 1
            r = candidates[0]
            body = data[r.body:r.end]
            assert r.class_guid == "AD719C1A-11AF-4537-BB41-030A9091D36B" and len(body) == 17
            assert struct.unpack_from("<I", body, 2)[0] == key and reference(body, 6) == settings["control_record_object_id"]
            native.append({"element_record_object_id": identity, "stored_key": key})
        # Compare a SET of cached geometry only. The existing body-to-ASM
        # associations are experimental, so they cannot establish instance IDs.
        cache_centers = []
        for body in stream["body_placement"]["bodies"]:
            points = body["component_vertex_positions_cm"]
            cache_centers.append([(min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)])
        expected_centers = [[1.5+p["translation_cm"][0], 0.5+p["translation_cm"][1],
                             0.5+p["translation_cm"][2]] for p in placements]
        checks = {"actual_api_matrix_multiset_matches": _same_matrix_set([p["matrix"] for p in placements], actual),
                  "getter_quantity_distance_symmetry_controls_match_native": all(settings[k] == sample["settings"][k] for k in ("quantity_one", "quantity_two", "distance_one_cm", "distance_two_cm", "symmetric_one", "symmetric_two")),
                  "element_and_body_counts_match": len(placements) == len(actual) == sample["settings"]["result_body_count"],
                  "leading_cached_body_center_multiset_matches_conditionally": _same_matrix_set(expected_centers, cache_centers),
                  "native_element_key_coverage_matches_quantity_product": len(native) == settings["quantity_one"]*settings["quantity_two"],
                  "settings_not_mutated": settings == before,
                  "no_per_placement_native_or_api_id": all(set(p) == {"logical_grid_coordinates", "translation_cm", "matrix", "signed_spacing_coefficients"} for p in placements)}
        assert all(checks.values()), (sample["file"], checks)
        report["samples"].append({"archive": str(archive.relative_to(root)), "checks": checks,
                                   "controls": {k: settings[k] for k in ("quantity_one", "quantity_two", "distance_one_cm", "distance_two_cm", "symmetric_one", "symmetric_two")},
                                   "native_elements": native, "api_elements": sample["pattern_elements"],
                                   "placement_set": placements, "leading_cached_body_centers_cm": cache_centers,
                                   "cache_evidence_scope": "Conditional corroboration from existing leading cached-ASM-root selection; body-to-ASM associations remain experimental. No native/API instance association inferred."})
        baseline = settings
    for label, updates in (("Extent rejected", {"distance_type": "Extent"}),
                           ("Negative spacing rejected", {"distance_one_cm": -2.5}),
                           ("Feature input rejected", {"pattern_entity_type": "Features"}),
                           ("Multiple input bodies rejected", {"input_count": 2}),
                           ("Inactive second direction rejected", {"quantity_two": 1}),
                           ("Nonempty suppression rejected", {"stored_suppressed_element_keys": [3]}),
                           ("Uncaptured custom direction rejected", {"direction_one_selection": {"entity": {"kind": "ConstructionAxis", "name": "Custom"}}})):
        candidate = copy.deepcopy(baseline)
        candidate.update(updates)
        try:
            rectangular_symmetry_translation_set(candidate)
        except ValueError as error:
            report["negative_checks"].append({"check": label, "passed": True, "reason": str(error)})
        else:
            raise AssertionError(label)
    report["limitations"] = ["Symmetric Extent, negative/zero spacing, inactive directions, custom axes, sketch-line directions, feature/multiple inputs and occurrence contexts lack symmetry getter contrasts and are rejected.",
                              "The helper returns analytic matrix sets; it does not read per-instance matrices or associate native keys, API IDs, result anchors or cached bodies with logical grid indices.",
                              "Body cache corroboration uses existing experimental leading-root selection and establishes no additional topology ownership.",
                              "Matrices remain in component coordinates and are never applied again to stored result body caches; no regeneration or joint solving is performed.",
                              "Rectangular symmetry evidence does not resolve the separate circular getter counterexamples."]
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", required=True)
    parser.add_argument("--zstd-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("rectangular-symmetry-decoding.json"))
    args = parser.parse_args()
    report = validate_fixtures(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"samples": len(report["samples"]), "negative_checks": len(report["negative_checks"]), "output": str(args.output)}))
