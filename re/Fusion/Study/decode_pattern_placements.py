"""Validated analytic rectangular placement sets, independent of body caches.

These matrices are calculated from decoded controls, not read as native matrices.
They have no proven correspondence to native element records, API element IDs,
result body anchors or ASM topology. Circular cases stay unresolved; symmetry
is limited to independently captured explicit-axis body patterns.
"""

import argparse
import copy
import json
import math
from pathlib import Path
import struct

from decode_sketch import reference, same
from decode_rectangular_symmetry import rectangular_symmetry_translation_set


ELEMENT = "AD719C1A-11AF-4537-BB41-030A9091D36B"
CONTROLLERS = {"RectangularPattern": "EA0E146E-3126-42F0-9280-0DE74AB17D78",
               "CircularPattern": "7493A99D-EDFC-4932-8B75-4120A8FA7875"}


def rectangular_translation_set(settings):
    """Return logical grid coordinates and matrices, without instance identities."""
    if settings.get("pattern_entity_type") not in ("Bodies", "Features"):
        raise ValueError("Placement computation supports observed body/feature inputs only")
    if settings.get("symmetric_one") is not False or settings.get("symmetric_two") is not False:
        raise ValueError("Symmetric rectangular placement getters have no captured contrast")
    if settings.get("stored_suppressed_element_keys") != []:
        raise ValueError("Rectangular suppressed-key/placement association is unverified")
    quantities = [settings.get("quantity_one"), settings.get("quantity_two")]
    if any(type(q) is not int or not 1 <= q <= 1024 for q in quantities) or not 2 <= math.prod(quantities) <= 1024:
        raise ValueError("Unsupported rectangular placement grid size")
    if settings.get("distance_type") not in ("Extent", "Spacing"):
        raise ValueError("Unsupported rectangular placement distance mode")
    steps = []
    for index, name in enumerate(("one", "two")):
        quantity = quantities[index]
        distance = settings.get("distance_"+name+"_cm")
        if not isinstance(distance, (int, float)) or not math.isfinite(distance):
            raise ValueError("Invalid rectangular placement distance")
        # A zero distance contributes no displacement, even when its stored
        # quantity repeats logical instances and the default axis is unknown.
        if quantity == 1 or distance == 0:
            steps.append([0.0, 0.0, 0.0])
            continue
        direction = settings.get("direction_"+name)
        selection = settings.get("direction_"+name+"_selection")
        if (not selection or not isinstance(direction, (list, tuple)) or len(direction) != 3
                or any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in direction)
                or not math.isclose(sum(x*x for x in direction), 1.0, abs_tol=1e-9)):
            raise ValueError("Active rectangular direction lacks a decoded explicit unit vector")
        step = distance/(quantity-1) if settings["distance_type"] == "Extent" else distance
        steps.append([step*x for x in direction])
    placements = []
    for v in range(quantities[1]):
        for u in range(quantities[0]):
            translation = [u*a+v*b for a, b in zip(*steps)]
            x, y, z = translation
            placements.append({"logical_grid_coordinates": [u, v], "translation_cm": translation,
                               "matrix": [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y,
                                          0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]})
    return placements


def decode_pattern_placements(data, records, features):
    """Run after decode_tools; return decoded placement sets and unresolved cases.

    The existing strict tool parsers establish control/selection ownership. This
    pass additionally verifies every exposed native element's bounded payload and
    controller backlink. It never mutates features or cached body placements.
    """
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {key: values[0] for key, values in grouped.items() if len(values) == 1}
    decoded, unresolved = [], []
    for feature in features:
        kind = feature["kind"]
        if kind not in CONTROLLERS:
            continue
        evidence = {}
        try:
            settings = feature.get("tool_settings", {})
            control_id = settings["control_record_object_id"]
            control = primary.get(control_id)
            if control is None or control.class_guid != CONTROLLERS[kind]:
                raise ValueError("Pattern placement controller missing, ambiguous or wrong class")
            ids = settings["element_record_object_ids"]
            keys = settings["stored_element_keys" if kind == "RectangularPattern" else "stored_element_ordinals"]
            if not ids or len(ids) != len(keys) or len(set(ids)) != len(ids):
                raise ValueError("Pattern placement element table missing or inconsistent")
            for identity, key in zip(ids, keys):
                record = primary.get(identity)
                if record is None or record.class_guid != ELEMENT:
                    raise ValueError("Pattern placement native element missing, ambiguous or wrong class")
                body = data[record.body:record.end]
                if (len(body) != 17 or body[:2] != b"\0\0"
                        or struct.unpack_from("<I", body, 2)[0] != key
                        or reference(body, 6) != control_id):
                    raise ValueError("Pattern placement element payload/key/controller mismatch")
            evidence = {"control_record_object_id": control_id,
                        "controller_payload_bytes": control.end-control.body,
                        "native_element_records": [{"object_id": identity, "stored_key_or_ordinal": key,
                                                    "payload_bytes": 17} for identity, key in zip(ids, keys)],
                        "native_matrix_evidence": "Bounded element records contain only header, key/ordinal and controller reference; validated controller schemas expose no per-element matrices. Other cache records are outside this claim."}
            if kind == "CircularPattern":
                raise ValueError("Circular API getter matrix sets disagree with ordinary equally spaced rotation sets in captured full/partial/symmetric fixtures; transform semantics unresolved")
            placements = (rectangular_symmetry_translation_set(settings)
                          if settings.get("symmetric_one") or settings.get("symmetric_two")
                          else rectangular_translation_set(settings))
            if len(placements) != len(ids):
                raise ValueError("Computed rectangular placement count disagrees with native element count")
            decoded.append({"feature_object_id": feature["object_id"], "kind": kind,
                            "source": "Analytically computed from decoded quantities, distances and explicit directions",
                            "coordinate_frame": "Native feature-control vectors; root-component API cases verified, other context relationships remain partial",
                            "matrix_convention": "Row-major 4x4, column-vector multiplication, translation in cm",
                            "placement_set": placements, "native_evidence": evidence,
                            "element_association": "Unresolved: no logical-grid-to-native-record, API-ID or result-body mapping asserted",
                            "cache_application": "Not applied: resulting body caches already contain their stored placements",
                            "scope": "Relative input placement set only; feature recomputation and generated geometry are not implemented"})
        except (ValueError, KeyError, IndexError, struct.error) as error:
            unresolved.append({"feature_object_id": feature["object_id"], "kind": kind,
                               "reason": str(error), "native_evidence": evidence})
    return {"decoded": decoded, "unresolved": unresolved,
            "scope": "Observed unsuppressed rectangular translation sets, including captured symmetric spacing/extent and input/direction variants; no instance/body identity association, cache modification, joint solving or geometry regeneration"}


def _same_matrix_set(one, two):
    remaining = list(two)
    for matrix in one:
        match = next((i for i, candidate in enumerate(remaining) if same(matrix, candidate)), None)
        if match is None:
            return False
        remaining.pop(match)
    return not remaining


def validate_fixtures(root, zstd_library):
    """Focused stored-reference/API getter checks; no Fusion/UI access required."""
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    def load(archive):
        members = read_members(archive, zstd_library)
        decoded = decode_basics(archive, zstd_library)
        streams = []
        for stream in decoded["streams"]:
            member = stream["member"]
            records, _ = design_records(members[member], members.get(member.replace("BulkStream.dat", "MetaStream.dat")))
            streams.append((members[member], records, stream["features"]))
        return streams

    report = {"api_version": "2705.1.30", "rectangular_samples": [], "circular_counterexamples": [],
              "negative_checks": [], "validation_command": "python3 decode_pattern_placements.py --validate --zstd-library <local libzstd path>",
              "interface": "decode_pattern_placements(data, records, features), after decode_tools; returns decoded/unresolved without mutating inputs"}
    folder = root/"rectmodes-a069f8f4b8a2"
    for sample in json.loads((folder/"ground_truth.json").read_text())["samples"]:
        archive = folder/sample["file"]
        streams = load(archive)
        outputs = [decode_pattern_placements(*args) for args in streams]
        items = [item for output in outputs for item in output["decoded"]]
        assert len(items) == 1 and not any(output["unresolved"] for output in outputs)
        item = items[0]
        computed = [p["matrix"] for p in item["placement_set"]]
        actual = [e["transform"] for e in sample["pattern_elements"]]
        checks = {"matrix_multisets_match_actual_api_getters": _same_matrix_set(computed, actual),
                  "all_native_elements_are_exact_17_byte_key_controller_records": all(e["payload_bytes"] == 17 for e in item["native_evidence"]["native_element_records"]),
                  "api_elements_are_unsuppressed": all(not e["is_suppressed"] for e in sample["pattern_elements"]),
                  "computed_matrices_have_no_native_or_api_identity": all(set(p) == {"logical_grid_coordinates", "translation_cm", "matrix"} for p in item["placement_set"])}
        assert all(checks.values()), (sample["file"], checks)
        report["rectangular_samples"].append({"archive": str(archive.relative_to(root)), "checks": checks,
                                                "placement_count": len(computed), "decoded": item})
        if sample["file"] == "body_one.f3d":
            base_data, base_records, base_features = next(args for args in streams if any(f["kind"] == "RectangularPattern" for f in args[2]))
            baseline = next(f for f in base_features if f["kind"] == "RectangularPattern")
    folder = root/"circularmodes-45f859c1f1b6"
    cases = {"body_full.f3d", "body_negative.f3d", "body_symmetric.f3d", "multiple_customaxis.f3d"}
    for sample in json.loads((folder/"ground_truth.json").read_text())["samples"]:
        if sample["file"] not in cases:
            continue
        outputs = [decode_pattern_placements(*args) for args in load(folder/sample["file"])]
        unresolved = [item for output in outputs for item in output["unresolved"]]
        assert len(unresolved) == 1 and not any(output["decoded"] for output in outputs)
        actual = [{"api_id": e["id"], "matrix": e["transform"],
                   "rotation_about_z_degrees_for_this_fixture": math.degrees(math.atan2(e["transform"][4], e["transform"][0]))}
                  for e in sample["pattern_elements"]]
        diagnostic = {}
        if not sample["settings"]["is_symmetric"]:
            # A comparison hypothesis only, never an emitted decoded placement.
            # These three fixtures all explicitly report a +Z axis.
            assert same(sample["settings"]["axis_direction"], [0, 0, 1])
            quantity = int(sample["settings"]["quantity"])
            angle = sample["settings"]["total_angle_radians"]
            full = math.isclose(abs(angle), 2*math.pi, abs_tol=1e-9)
            step = angle/(quantity if full else quantity-1)
            x, y, _ = sample["settings"]["axis_origin_cm"]
            hypothesis = []
            for i in range(quantity):
                c, s = math.cos(i*step), math.sin(i*step)
                hypothesis.append([c, -s, 0, x-c*x+s*y, s, c, 0, y-s*x-c*y,
                                   0, 0, 1, 0, 0, 0, 0, 1])
            matches = _same_matrix_set(hypothesis, [item["matrix"] for item in actual])
            assert not matches
            diagnostic = {"comparison_hypothesis": "Ordinary equally spaced +Z rotations about API-reported axis, including identity; not accepted as decoded output",
                          "hypothesis_rotation_angles_degrees": [math.degrees(i*step) for i in range(quantity)],
                          "hypothesis_and_getter_matrix_multisets_match": matches}
        else:
            identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
            assert not same(actual[0]["matrix"], identity)
            diagnostic = {"first_getter_matrix_is_identity": False,
                          "sdk_contract": "Local PatternElement.transform documentation says the first element returns identity; captured symmetric getter differs. No corrective transform rule inferred."}
        report["circular_counterexamples"].append({"archive": str((folder/sample["file"]).relative_to(root)),
                                                   "api_settings": sample["settings"], "api_getters": actual,
                                                   "diagnostic": diagnostic, "unresolved": unresolved[0]})
    for label, updates in (("Symmetric grid rejected", {"symmetric_one": True}),
                           ("Nonempty suppression rejected", {"stored_suppressed_element_keys": [3]}),
                           ("Active direction without explicit selection rejected", {"direction_one_selection": None}),
                           ("Nonunit active direction rejected", {"direction_one": [2, 0, 0]}),
                           ("Nonfinite distance rejected", {"distance_one_cm": float("nan")})):
        settings = copy.deepcopy(baseline["tool_settings"])
        settings.update(updates)
        try:
            rectangular_translation_set(settings)
        except ValueError as error:
            report["negative_checks"].append({"check": label, "passed": True, "reason": str(error)})
        else:
            raise AssertionError(label)
    corrupted = bytearray(base_data)
    element_id = baseline["tool_settings"]["element_record_object_ids"][0]
    record = next(r for r in base_records if r.is_primary and r.object_id == element_id)
    struct.pack_into("<Q", corrupted, record.body+7, baseline["object_id"])
    rejected = decode_pattern_placements(bytes(corrupted), base_records, base_features)
    assert not rejected["decoded"] and rejected["unresolved"]
    report["negative_checks"].append({"check": "Native element controller backlink corruption rejected", "passed": True,
                                      "reason": rejected["unresolved"][0]["reason"]})
    report["limitations"] = ["Native grid key sets and API getter matrix multisets are verified separately; no element ID associations follow from matching geometry.",
                              "Circular getter evidence is preserved without guessing a correction or treating its matrices as generated body placements.",
                              "Rectangular symmetry, nonempty suppression, occurrence input/context placement and unsupported direction selections remain unresolved.",
                              "Analytic matrices are relative component-space translations and must not be applied again to already transformed result body caches.",
                              "Matrix sets do not regenerate feature geometry; Adjust compute may change generated geometry even with the same placement set."]
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", required=True)
    parser.add_argument("--zstd-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("pattern-placement-decoding.json"))
    args = parser.parse_args()
    result = validate_fixtures(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"report": str(args.output), "rectangular_samples": len(result["rectangular_samples"]),
                      "circular_counterexamples": len(result["circular_counterexamples"]), "negative_checks": len(result["negative_checks"])}))
