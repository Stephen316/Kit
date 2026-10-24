"""Observed rectangular symmetry translation sets, without instance identities.

Captured variants include signed spacing, positive extent, oblique construction
axes, two-body inputs and Identical feature inputs. Uncaptured combinations are
rejected. Native keys, API IDs and result bodies stay separate.
"""

import argparse
import copy
import json
import math
from pathlib import Path

from decode_sketch import same


SCOPE = "Observed symmetric rectangular spacing/extent placement sets and captured input/direction variants; no instance ID association, cache application or geometry regeneration"


def rectangular_symmetry_translation_set(settings):
    """Return the observed symmetric grid translation set after strict tool parsing.

    For a symmetric axis, logical index i uses spacing coefficient
    i-floor((quantity-1)/2). Odd quantities balance around the seed; even
    quantities leave one additional positive coefficient. Spacing uses the
    distance directly. Symmetric Extent divides it by floor(quantity/2), while
    nonsymmetric Extent divides by quantity-1. This is a getter/geometry
    validated formula, not a key/ordinal interpretation.
    """
    flags = [settings.get("symmetric_one"), settings.get("symmetric_two")]
    if any(type(flag) is not bool for flag in flags) or not any(flags):
        raise ValueError("Expected at least one explicit rectangular symmetry flag")
    mode = settings.get("distance_type")
    if mode not in ("Spacing", "Extent"):
        raise ValueError("Unsupported symmetric placement distance mode")
    quantities = [settings.get("quantity_one"), settings.get("quantity_two")]
    if any(type(q) is not int or not 2 <= q <= 1024 for q in quantities) or math.prod(quantities) > 1024:
        raise ValueError("Symmetric placement contrasts require two active grid directions")
    distances, directions, entities, selections = [], [], [], []
    for name in ("one", "two"):
        distance = settings.get("distance_"+name+"_cm")
        if not isinstance(distance, (int, float)) or not math.isfinite(distance) or distance == 0:
            raise ValueError("Symmetric zero/nonfinite distance getter contrast unavailable")
        selection = settings.get("direction_"+name+"_selection") or {}
        entity = selection.get("entity", {})
        direction = settings.get("direction_"+name, [])
        if (entity.get("kind") != "ConstructionAxis" or not same(entity.get("origin_cm", []), [0, 0, 0])
                or len(direction) != 3 or not same(entity.get("direction", []), direction)
                or not math.isclose(sum(x*x for x in direction), 1, abs_tol=1e-9)
                or not math.isclose(direction[2], 0, abs_tol=1e-9)):
            raise ValueError("Symmetric direction lacks an observed explicit zero-origin planar construction axis")
        distances.append(distance)
        directions.append(direction)
        entities.append(entity)
        selections.append(selection)
    canonical = (entities[0].get("name") == "X" and entities[1].get("name") == "Y"
                 and same(directions[0], [1, 0, 0]) and same(directions[1], [0, 1, 0])
                 and entities[0].get("origin_container_object_id") is not None
                 and entities[0].get("origin_container_object_id") == entities[1].get("origin_container_object_id"))
    oblique = (all(entity.get("feature_object_id") is not None for entity in entities)
               and selections[0].get("namespace_text") is not None
               and selections[0].get("namespace_text") == selections[1].get("namespace_text"))
    entity_type, count = settings.get("pattern_entity_type"), settings.get("input_count")
    positive = all(distance > 0 for distance in distances)
    if entity_type == "Bodies" and count == 1:
        if mode == "Extent" and (not canonical or not positive):
            raise ValueError("Symmetric Extent contrasts cover positive distances on component X/Y axes only")
        if mode == "Spacing" and not (canonical or oblique and positive):
            raise ValueError("Uncaptured symmetric body direction/distance combination")
    elif entity_type == "Bodies" and count == 2:
        if mode != "Spacing" or not canonical or not positive:
            raise ValueError("Two-body symmetry contrast covers positive Spacing on component X/Y axes only")
    elif entity_type == "Features" and count == 1:
        if mode != "Spacing" or not canonical or not positive or settings.get("pattern_compute_option") != "Identical":
            raise ValueError("Feature symmetry contrast covers Identical positive Spacing on component X/Y axes only")
    else:
        raise ValueError("Uncaptured symmetric pattern entity type or input count")
    # Local import keeps the helper safe to import from the placement module.
    from decode_pattern_placements import rectangular_translation_set
    nonsymmetric = dict(settings, symmetric_one=False, symmetric_two=False)
    steps = [distance/(q//2 if flag else q-1) if mode == "Extent" else distance
             for distance, q, flag in zip(distances, quantities, flags)]
    if mode == "Extent":
        for name, step, quantity in zip(("one", "two"), steps, quantities):
            nonsymmetric["distance_"+name+"_cm"] = step*(quantity-1)
    placements = rectangular_translation_set(nonsymmetric)
    center = [(q-1)//2 if flag else 0 for q, flag in zip(quantities, flags)]
    shift = [sum(c*step*direction[i] for c, step, direction in zip(center, steps, directions)) for i in range(3)]
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

    fixtures = []
    for name, expected_count in (("rectsymmetry-f09c57dcfd51", 4), ("rectsymholdouts-cf85ce4a0382", 6)):
        folder = root/name
        truth = json.loads((folder/"ground_truth.json").read_text())
        assert (folder/"complete.txt").is_file() and not truth["errors"] and len(truth["samples"]) == expected_count
        fixtures.extend((folder, sample) for sample in truth["samples"])
    report = {"scope": SCOPE, "api_version": truth["fusion_version"], "samples": [], "negative_checks": [],
              "interface": "rectangular_symmetry_translation_set(settings) -> placement list; raises ValueError outside observed scope; call after strict decode_rectangular_pattern_modes",
              "validation_command": "python3 decode_rectangular_symmetry.py --validate --zstd-library <local libzstd path>"}
    for folder, sample in fixtures:
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
        seed_centers = [box["center_cm"] for box in sample["seed_body_boxes"]] if "seed_body_boxes" in sample else [[1.5, 0.5, 0.5]]
        expected_centers = [[seed[i]+p["translation_cm"][i] for i in range(3)] for seed in seed_centers for p in placements]
        checks = {"actual_api_matrix_multiset_matches": _same_matrix_set([p["matrix"] for p in placements], actual),
                  "getter_quantity_distance_symmetry_controls_match_native": all(settings[k] == sample["settings"][k] for k in ("quantity_one", "quantity_two", "distance_one_cm", "distance_two_cm", "symmetric_one", "symmetric_two")),
                  "element_and_body_counts_match": len(placements) == len(actual) and len(expected_centers) == sample["settings"]["result_body_count"],
                  "directions_match_actual_getters": all(same(settings["direction_"+name], sample["settings"]["direction_"+name]) for name in ("one", "two")),
                  "leading_cached_body_center_multiset_matches_conditionally": _same_matrix_set(expected_centers, cache_centers),
                  "native_element_key_coverage_matches_quantity_product": len(native) == settings["quantity_one"]*settings["quantity_two"],
                  "settings_not_mutated": settings == before,
                  "no_per_placement_native_or_api_id": all(set(p) == {"logical_grid_coordinates", "translation_cm", "matrix", "signed_spacing_coefficients"} for p in placements)}
        if "result_body_boxes" in sample:
            checks["independent_actual_api_body_center_multiset_matches"] = _same_matrix_set(expected_centers, [box["center_cm"] for box in sample["result_body_boxes"]])
        main_placements = [p["matrix"] for item in stream["pattern_placements"]["decoded"]
                           if item["feature_object_id"] == feature["object_id"] for p in item["placement_set"]]
        checks["main_reader_matrix_multiset_matches_getters"] = _same_matrix_set(main_placements, actual)
        assert all(checks.values()), (sample["file"], checks)
        extent_note = None
        if settings["distance_type"] == "Extent":
            # Preserve the rejected nonsymmetric-extent scaling hypothesis.
            naive = []
            q1, q2 = settings["quantity_one"], settings["quantity_two"]
            for v in range(q2):
                for u in range(q1):
                    coefficients = [u-((q1-1)//2 if settings["symmetric_one"] else 0), v-((q2-1)//2 if settings["symmetric_two"] else 0)]
                    naive.append([coefficients[0]*settings["distance_one_cm"]/(q1-1), coefficients[1]*settings["distance_two_cm"]/(q2-1), 0])
            assert not _same_matrix_set(naive, [p["translation_cm"] for p in placements])
            extent_note = {"rejected_hypothesis": "Dividing every extent by quantity-1, including symmetric directions", "rejected_hypothesis_matches_getters": False,
                           "validated_step_divisors": [q//2 if settings["symmetric_"+name] else q-1 for q, name in ((q1, "one"), (q2, "two"))]}
        report["samples"].append({"archive": str(archive.relative_to(root)), "checks": checks,
                                   "controls": {k: settings[k] for k in ("quantity_one", "quantity_two", "distance_one_cm", "distance_two_cm", "symmetric_one", "symmetric_two")},
                                   "native_elements": native, "api_elements": sample["pattern_elements"],
                                   "placement_set": placements, "leading_cached_body_centers_cm": cache_centers,
                                   "extent_diagnostic": extent_note,
                                   "api_seed_body_boxes": sample.get("seed_body_boxes"), "api_result_body_boxes": sample.get("result_body_boxes"),
                                   "seed_center_evidence": "Actual API bounding-box getters" if "seed_body_boxes" in sample else "Initial fixture creation geometry; independent API boxes were not captured in this first four-case set",
                                   "cache_evidence_scope": "Conditional corroboration from existing leading cached-ASM-root selection; body-to-ASM associations remain experimental. No native/API instance association inferred."})
        baseline = settings
    for label, updates in (("Negative Extent rejected", {"input_count": 1, "distance_type": "Extent", "distance_one_cm": -6.0}),
                           ("Zero spacing rejected", {"distance_one_cm": 0.0}),
                           ("Uncaptured feature compute mode rejected", {"input_count": 1, "pattern_entity_type": "Features", "pattern_compute_option": "Adjust"}),
                           ("Three input bodies rejected", {"input_count": 3}),
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
    report["limitations"] = ["Negative/zero Extent, zero Spacing, inactive directions, sketch-line directions, out-of-plane/custom-offset axes, occurrence contexts and nonempty suppression lack symmetry getter contrasts and are rejected.",
                              "Extent is limited to single-body positive distances on component X/Y axes. Oblique axes are limited to single-body positive Spacing. Feature inputs require a single Identical input with positive Spacing on X/Y; multiple body inputs require exactly two bodies with positive Spacing on X/Y. Uncaptured combinations are rejected.",
                              "The helper returns analytic matrix sets; it does not read per-instance matrices or associate native keys, API IDs, result anchors or cached bodies with logical grid indices.",
                              "Body cache corroboration uses existing experimental leading-root selection and establishes no additional topology ownership.",
                              "Matrices remain in component coordinates and are never applied again to stored result body caches; no regeneration or joint solving is performed.",
                              "Rectangular symmetry evidence does not resolve the separate circular getter counterexamples."]
    report["totals"] = {"archives": len(report["samples"]),
                         "placement_matrices": sum(len(s["placement_set"]) for s in report["samples"]),
                         "archives_with_independent_actual_api_body_box_checks": sum("independent_actual_api_body_center_multiset_matches" in s["checks"] for s in report["samples"])}
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
