"""Check native numeric conversion limits without introducing nonfinite JSON."""

import argparse
import copy
import json
import math
from pathlib import Path
import struct
import sys

from decode_parameters import decode_stream
from decode_sketch import attributes, decode_sketches
from validate_mesh_remesh import load

# saved captures must resolve independently of the current directory
ROOT = Path(__file__).resolve().parent


# malformed operands must exercise the original native byte reader
def changed_float(data, offset, value):
    changed = bytearray(data)
    struct.pack_into("<d", changed, offset, value)
    assert len(changed) == len(data)
    return bytes(changed)


# numeric diagnostics must identify the rejected native record precisely
def rejected_record(rows, identity, offset, conversion):
    (selected,) = [row for row in rows if row["object_id"] == identity]
    if offset is not None:
        assert selected["offset"] == offset
    if conversion:
        assert "conversion exceeds finite range" in selected["reason"]
    else:
        assert selected["reason"]
    return selected


# conversion boundaries must preserve supported values and expose overflow explicitly
def validate(root, zstd_library):
    report = {
        "scope": "Native parameter and Circle display conversions with explicit unsupported diagnostics",
        "parameter_cases": [],
        "circle_cases": [],
        "main_reader_calls": 0,
        "live_Fusion_calls": 0,
    }
    archive = "holes-926347c1eaa8/simple.f3d"
    data, records, features, _, _ = load(root, archive, zstd_library)
    original, rejected = decode_stream(data, records)
    assert not rejected
    assert len(original) == 5
    by_identity = {item["parameter_object_id"]: item for item in original}
    record_offsets = {
        record.object_id: record.start for record in records if record.is_primary
    }
    for units, output, factor in (
        ("mm", "hypothesized_value_mm", 10.0),
        ("deg", "hypothesized_value_degrees", math.degrees(1.0)),
    ):
        (target,) = [
            item
            for item in original
            if item["display_units"] == units and item["parameter_name"] in ("d1", "d2")
        ]
        identity = target["parameter_object_id"]
        boundary = sys.float_info.max / factor
        cases = [
            ("zero", 0.0, True),
            ("positive", 1.0, True),
            ("negative", -1.0, True),
            ("tiny", 1e-310, True),
            ("finite_boundary", boundary, True),
            ("negative_finite_boundary", -boundary, True),
            ("adjacent_overflow", math.nextafter(boundary, math.inf), False),
            ("negative_adjacent_overflow", -math.nextafter(boundary, math.inf), False),
            ("finite_overflow", 1e308, False),
            ("negative_finite_overflow", -1e308, False),
            ("infinity", math.inf, False),
            ("not_a_number", math.nan, False),
        ]
        for label, value, accepted in cases:
            mutated = changed_float(data, target["value_offset"], value)
            decoded, failures = decode_stream(mutated, records)
            json.dumps({"decoded": decoded, "rejected": failures}, allow_nan=False)
            remaining = {
                item["parameter_object_id"]: item
                for item in decoded
                if item["parameter_object_id"] != identity
            }
            assert remaining == {
                key: item for key, item in by_identity.items() if key != identity
            }
            diagnostic = None
            if accepted:
                (actual,) = [
                    item for item in decoded if item["parameter_object_id"] == identity
                ]
                expected = dict(target, raw_float64=value)
                expected[output] = math.degrees(value) if units == "deg" else value * 10
                assert actual == expected
                assert math.isfinite(actual[output])
                assert failures == []
            else:
                assert identity not in {item["parameter_object_id"] for item in decoded}
                assert len(failures) == 1
                diagnostic = rejected_record(
                    failures, identity, record_offsets[identity], math.isfinite(value)
                )
            report["parameter_cases"].append(
                {
                    "archive": archive,
                    "case": label,
                    "display_units": units,
                    "parameter_object_id": identity,
                    "native_value_offset": target["value_offset"],
                    "mutated_value_repr": repr(value),
                    "accepted": accepted,
                    "other_parameter_dictionaries_unchanged": True,
                    "strict_JSON": True,
                    "diagnostic": diagnostic,
                }
            )
    archive = "sketches-0ccea2ac0f9c/baseline.f3d"
    data, records, features, _, _ = load(root, archive, zstd_library)
    original_summary = decode_sketches(data, records, features)
    assert original_summary["unsupported_curves"] == []
    (sketch,) = [item for item in features if item["kind"] == "Sketch"]
    (circle,) = [item for item in sketch["geometry"] if item["kind"] == "Circle"]
    (record,) = [
        item
        for item in records
        if item.is_primary and item.object_id == circle["object_id"]
    ]
    _, cursor = attributes(data[record.body : record.end], 2)
    offset = record.body + cursor + 9 * 8
    assert struct.unpack_from("<d", data, offset)[0] == circle["radius_cm"]
    boundary = sys.float_info.max / 10
    cases = [
        ("ordinary", 0.25, True),
        ("tiny", 1e-310, True),
        ("finite_boundary", boundary, True),
        ("adjacent_overflow", math.nextafter(boundary, math.inf), False),
        ("finite_overflow", 1e308, False),
        ("zero", 0.0, False),
        ("negative", -1.0, False),
        ("infinity", math.inf, False),
        ("not_a_number", math.nan, False),
    ]
    for label, radius, accepted in cases:
        mutated = changed_float(data, offset, radius)
        fresh = copy.deepcopy(features)
        summary = decode_sketches(mutated, records, fresh)
        (actual_sketch,) = [item for item in fresh if item["kind"] == "Sketch"]
        json.dumps({"features": fresh, "summary": summary}, allow_nan=False)
        assert [
            item
            for item in actual_sketch["geometry"]
            if item["object_id"] != circle["object_id"]
        ] == [
            item
            for item in sketch["geometry"]
            if item["object_id"] != circle["object_id"]
        ]
        diagnostic = None
        if accepted:
            (actual,) = [
                item
                for item in actual_sketch["geometry"]
                if item["object_id"] == circle["object_id"]
            ]
            assert actual == dict(circle, radius_cm=radius, radius_mm=radius * 10)
            assert summary == original_summary
        else:
            assert circle["object_id"] not in {
                item["object_id"] for item in actual_sketch["geometry"]
            }
            assert len(summary["unsupported_curves"]) == 1
            diagnostic = rejected_record(
                summary["unsupported_curves"],
                circle["object_id"],
                None,
                math.isfinite(radius) and radius > 0,
            )
        report["circle_cases"].append(
            {
                "archive": archive,
                "case": label,
                "curve_object_id": circle["object_id"],
                "native_radius_offset": offset,
                "mutated_value_repr": repr(radius),
                "accepted": accepted,
                "other_geometry_dictionaries_unchanged": True,
                "strict_JSON": True,
                "diagnostic": diagnostic,
            }
        )
    report["summary"] = {
        "saved_archives": 2,
        "actual_byte_mutations": len(report["parameter_cases"])
        + len(report["circle_cases"]),
        "accepted_cases": sum(
            item["accepted"]
            for item in report["parameter_cases"] + report["circle_cases"]
        ),
        "explicit_rejections": sum(
            not item["accepted"]
            for item in report["parameter_cases"] + report["circle_cases"]
        ),
        "all_passed": True,
    }
    return report


if __name__ == "__main__":

    # explicit command options keep validation independent of local defaults
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zstd-library")
    parser.add_argument("--output", type=Path, required=True)

    # caller options must not modify native capture inputs
    arguments = parser.parse_args()

    # machine readable evidence keeps validation failures visible to later audits
    report = validate(ROOT, arguments.zstd_library)
    arguments.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report["summary"]))
