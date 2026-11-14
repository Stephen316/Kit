import argparse
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory

from Corpus import git
from SolidworksCensusCompare import (
    compare, require_boss_directions, require_equation_bindings, require_rectangle_edges,
)
from SolidworksCensusInputs import capture_inputs, digest
from SolidworksCensusLengths import require_resolved_lengths
from SolidworksCensusRead import native_read, neutral_read


def run_case(root, manifest, directory, case, revision, tolerance):
    recipe, asset, content, evidence, measured = case
    native = native_read(content, asset["path"])
    neutral = neutral_read(root, manifest, asset, directory / Path(asset["path"]).stem, revision)
    if neutral["status"] == "decoded" and native["status"] == "decoded":
        boundary = "both_decoded"
    elif neutral["status"] == "reader_timeout":
        boundary = "reader_timeout"
    elif native["status"] == "decoded":
        boundary = "reader_rejected_after_native_decode"
    elif neutral["status"] == "decoded":
        boundary = "native_inspection_disagrees_with_reader"
    else:
        boundary = "native_decode_failed"
    return {
        "recipe_id": recipe, "asset": asset, "capture_evidence": evidence,
        "boundary": boundary, "native": native, "neutral": neutral,
        "measured": {
            "configuration": measured["configuration"],
            "volume_mm3": measured["volume_mm3"],
            "center_of_mass_mm": measured["center_of_mass_mm"],
            "sketch_sections": [
                {
                    "name": sketch["name"], "area_mm2": sketch["section_area_mm2"],
                    "center_mm": sketch["section_center_world_mm"], "fully_defined": sketch["fully_defined"],
                }
                for sketch in measured["sketches"]
            ],
        },
        "comparisons": compare(measured, native, neutral, tolerance, Path(asset["path"]).name),
    }


def run(root, output):
    if output.exists():
        raise ValueError("select a new census output path")
    revision = git(root, "rev-parse", "HEAD").decode().strip()
    captures, tolerance = capture_inputs(root, revision)
    sys.path.insert(0, str(root / "src"))
    with TemporaryDirectory(prefix="kit-a04c-") as temporary:
        directory = Path(temporary)
        manifest = directory / "Discovery.json"
        manifest.write_text(json.dumps({
            "manifest_version": 1,
            "source_revision": revision,
            "assets": [case[1] for case in captures],
        }, sort_keys=True), encoding="utf-8")

        def inspect(case):
            return run_case(root, manifest, directory, case, revision, tolerance)

        with ThreadPoolExecutor(max_workers=4) as workers:
            findings = list(workers.map(inspect, captures))
        manifest_sha = digest(manifest.read_bytes())

    boundaries = Counter(item["boundary"] for item in findings)
    comparisons = Counter(comparison["status"] for item in findings for comparison in item["comparisons"])
    report = {
        "format_version": 1,
        "revision": revision,
        "scope": "SOLIDWORKS P01/P03/P04 discovery only",
        "manifest_sha256": manifest_sha,
        "length_comparison_tolerance_mm": tolerance,
        "native_acceptance": "not_established",
        "semantic_qualification": "unverified",
        "summary": {"files": len(findings), "boundaries": dict(boundaries), "comparisons": dict(comparisons)},
        "captures": findings,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as target:
        json.dump(report, target, indent=2, sort_keys=True, allow_nan=False)
        target.write("\n")
    print(json.dumps({"revision": revision, "report": str(output), **report["summary"]}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description="Census the pinned SOLIDWORKS discovery captures")
    outputs = parser.add_mutually_exclusive_group(required=True)
    outputs.add_argument("--output", type=Path)
    outputs.add_argument("--check-directions", type=Path)
    outputs.add_argument("--check-equations", type=Path)
    outputs.add_argument("--check-rectangle-edges", type=Path)
    outputs.add_argument("--check-resolved-lengths", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    check_report = args.check_equations or args.check_directions or args.check_rectangle_edges or args.check_resolved_lengths
    if check_report is not None:
        report = json.loads(check_report.read_bytes())
        revision = git(root, "rev-parse", "HEAD").decode().strip()
        if report["revision"] != revision:
            raise ValueError("discovery check requires a census from this revision")
        checks = (
            (args.check_equations, require_equation_bindings),
            (args.check_directions, require_boss_directions),
            (args.check_rectangle_edges, require_rectangle_edges),
            (args.check_resolved_lengths, require_resolved_lengths),
        )
        check = next(check for option, check in checks if option is not None)
        check(report["captures"])
    else:
        run(root, args.output.resolve())


if __name__ == "__main__":
    main()
