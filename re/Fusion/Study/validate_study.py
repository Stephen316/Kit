"""Check the experimental reader against API-generated ground truth."""

import argparse
import json
import math
from pathlib import Path

from decode_parameters import decode_file


def validate(originals, holdouts, library):
    results, failures = [], []
    cases = []
    original_truth = json.loads((originals / "inspection.json").read_text())
    holdout_truth = json.loads((holdouts / "ground_truth.json").read_text())
    for sample in original_truth["samples"]:
        cases.append((originals / sample["file"], [{
            "api_depth_cm": sample["api_depth_cm"], "draft_degrees": 0,
        }]))
    for sample in holdout_truth["samples"]:
        cases.append((holdouts / sample["file"], sample["extrusions"]))
    for path, expected in cases:
        result = decode_file(path, library)
        parameters = [p for s in result["streams"] for p in s["parameters"]]
        rejected = [p for s in result["streams"] for p in s["rejected"]]
        depths = [p for p in parameters if p["role"] == "AlongDistance"]
        angles = [p for p in parameters if p["role"] == "TaperAngle"]
        problems = []
        if rejected or len(depths) != len(expected) or len(angles) != len(expected):
            problems.append("Record counts or structural validation differ")
        expected_depths = sorted(e["api_depth_cm"] for e in expected)
        if len(depths) == len(expected):
            actual_depths = sorted(p["raw_float64"] for p in depths)
            if not all(math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
                       for a, b in zip(actual_depths, expected_depths)):
                problems.append("Decoded signed depths differ from Fusion API values")
        for item in expected:
            if "parameter_name" not in item:
                continue
            matches = [p for p in depths if p["parameter_name"] == item["parameter_name"]]
            if len(matches) != 1:
                problems.append("API parameter name not uniquely recovered")
            elif (not math.isclose(matches[0]["raw_float64"], item["api_depth_cm"], abs_tol=1e-12)
                  or matches[0]["expression_candidates"] != [item["expression"]]):
                problems.append("API parameter value or expression differs")
        if len(angles) == len(expected):
            actual = sorted(p["hypothesized_value_degrees"] for p in angles)
            wanted = sorted(e["draft_degrees"] for e in expected)
            if not all(math.isclose(a, b, abs_tol=1e-12) for a, b in zip(actual, wanted)):
                problems.append("Draft angles differ from generated settings")
        result["validation"] = "pass" if not problems else "fail"
        result["validation_errors"] = problems
        result["reference_extrusions"] = expected
        results.append(result)
        failures.extend(f"{path}: {p}" for p in problems)
    return {
        "scope": "One Fusion version; generated circle-based blind extrusions only",
        "files_checked": len(cases),
        "parameter_records_checked": sum(len(s["parameters"]) for r in results for s in r["streams"]),
        "independent_holdout_files": len(holdout_truth["samples"]),
        "status": "pass" if not failures else "fail", "failures": failures,
        "limitations": [
            "Record discovery uses observed semantic labels; no complete binary grammar.",
            "No decoded extrusion-to-parameter ownership graph; names matched to API evidence only.",
            "No sketch, profile, topology, body geometry or general end-condition decoder.",
            "No writer or modified-file loading test; no compatibility claim for other Fusion versions.",
            "Draft values checked against generation inputs; depth and expressions against API readings.",
        ],
        "results": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("originals", type=Path)
    parser.add_argument("holdouts", type=Path)
    parser.add_argument("--zstd-library")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate(args.originals, args.holdouts, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps({key: report[key] for key in (
        "status", "files_checked", "parameter_records_checked", "independent_holdout_files", "failures"
    )}, indent=2))
    raise SystemExit(0 if report["status"] == "pass" else 1)
