"""Compare licensed SOLIDWORKS and historical Fusion final bodies for P04."""

import argparse
import json
import math
import re
import sys
from pathlib import Path, PurePosixPath

from FusionCutExtentEvidence import (
    REVISION,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    p04_capture,
)
from FusionCutSketchEvidence import historical_observations
from PairedCaptureIntake import GitSnapshot, inspect_capture, require, sha256

SOLIDWORKS_RECEIPT = (
    "re/automation/PairedCaptures/P04/solidworks-c1986308375a/receipt.json"
)
COLLECTOR = "re/automation/PairedCaptures/SolidWorksAuthoring/P04Readback.cs"
SOLIDWORKS_BUILD = "34.4.1.1011"


# the supplied receipt digest binds the private measurement and independently staged plan
def document(path, digest):
    require(0 < path.stat().st_size <= 32 * 1024 * 1024, "invalid readback file size")
    data = path.read_bytes()
    require(sha256(data) == digest, f"readback digest mismatch for {path.name}")
    return GitSnapshot.parse_document(data, path.name)


# normalize dimensional quantities while preserving exact native topology counts
def solidworks_body(observation):
    body = observation["final_body"]
    require(body["solid_body_count"] == 1, "expected one measured SOLIDWORKS solid")
    return {
        "counts": [body[f"{name}_count"] for name in ("face", "edge", "vertex")],
        "bounds_mm": [
            [value * 1000 for value in body[f"bounds_{bound}_m"]]
            for bound in ("min", "max")
        ],
        "volume_mm3": body["volume_m3"] * 1e9,
        "center_of_mass_mm": [value * 1000 for value in body["center_of_mass_m"]],
    }


# the original Fusion collection reports bounds and topology at its recorded lifecycle point
def fusion_body(observation):
    require(observation["body_count"] == 1, "expected one measured Fusion body")
    (body,) = observation["bodies"]
    require(body["solid"] is True, "expected one measured Fusion solid")
    return {
        "counts": [body[name] for name in ("faces", "edges", "vertices")],
        "bounds_mm": body["bounding_box_mm"],
        "volume_mm3": body["volume_mm3"],
        "center_of_mass_mm": observation["center_of_mass_mm"],
    }


# failed correspondence remains visible separately for the measured fields
def compare(left, right, tolerances):
    for body in (left, right):
        require(
            all(type(value) is int and value > 0 for value in body["counts"]),
            "invalid measured topology counts",
        )
        lower, upper = body["bounds_mm"]
        center = body["center_of_mass_mm"]
        require(
            len(lower) == len(upper) == len(center) == 3
            and all(math.isfinite(number) for number in [*lower, *upper, *center])
            and all(a < b for a, b in zip(lower, upper, strict=True))
            and math.isfinite(body["volume_mm3"])
            and body["volume_mm3"] > 0,
            "invalid measured solid geometry",
        )
    bounds = max(
        abs(a - b)
        for left_bound, right_bound in zip(
            left["bounds_mm"], right["bounds_mm"], strict=True
        )
        for a, b in zip(left_bound, right_bound, strict=True)
    )
    center = math.dist(left["center_of_mass_mm"], right["center_of_mass_mm"])
    volume = abs(left["volume_mm3"] - right["volume_mm3"])
    volume_limit = max(
        tolerances["volume_mm3_absolute"],
        tolerances["volume_relative"] * max(left["volume_mm3"], right["volume_mm3"]),
    )
    length_limit = tolerances["length_mm_absolute"]
    return {
        "counts_exact": left["counts"] == right["counts"],
        "maximum_bound_difference_mm": bounds,
        "center_difference_mm": center,
        "volume_difference_mm3": volume,
        "within_declared_tolerances": (
            bounds <= length_limit and center <= length_limit and volume <= volume_limit
        ),
    }


# bind every observed native part to the same original recipe and immutable capture roster
def report(directory, receipt_digest):
    git, fusion = p04_capture()
    specification = git.document(REVISION, SPECIFICATION)
    recipe = next(item for item in specification["recipes"] if item["id"] == "P04")
    solidworks = inspect_capture(
        git,
        REVISION,
        SOLIDWORKS_RECEIPT,
        recipe,
        "solidworks",
        specification,
        SPECIFICATION_SHA256,
    )
    receipt = document(directory / "receipt.json", receipt_digest)
    plan = document(directory / "plan.json", receipt["plan_sha256"])
    measurements = document(
        directory / "measurements.json", receipt["measurements_sha256"]
    )
    require(
        receipt["schema"] == measurements["schema"] == 1
        and receipt["status"] == "observed"
        and receipt["observed_files"] == receipt["supporting_faces_verified"] == 11
        and measurements["plan_sha256"] == receipt["plan_sha256"]
        and measurements["source_bytes_verified_after_readback"] is True,
        "readback did not complete with pinned source bytes",
    )
    source = plan["source_revision"]
    require(re.fullmatch(r"[0-9a-f]{40}", source), "invalid source commit")
    require(
        plan["collector"]["path"] == COLLECTOR
        and sha256(git.blob(source, COLLECTOR)) == plan["collector"]["sha256"]
        and plan["existing_receipt"]["sha256"] == solidworks["receipt"]["sha256"]
        and plan["existing_measurements"]["sha256"]
        == solidworks["measurements"]["sha256"]
        and solidworks["canonical_recipe_sha256"] == fusion["canonical_recipe_sha256"],
        "readback does not match the pinned collector and P04 recipe",
    )
    run = measurements["run"]
    require(
        run["status"] == "observed"
        and run["owned_process_exit_observed"] is True
        and run["control_before"]["status"]
        == run["control_after"]["status"]
        == "observed",
        "native readback process did not exit after its observations",
    )
    require(
        run["application"]["build"] == SOLIDWORKS_BUILD,
        "unexpected SOLIDWORKS build",
    )
    native = {row["file"]: row for row in run["observations"]}
    archived = historical_observations(
        fusion, git.document(REVISION, fusion["measurements"]["path"])
    )
    fusion_files = {row["variant"]: row["sha256"] for row in fusion["native_files"]}
    require(
        set(native)
        == set(plan["native_files"])
        == {PurePosixPath(row["path"]).name for row in solidworks["native_files"]}
        and set(archived)
        == set(fusion_files)
        == {row["variant"] for row in solidworks["native_files"]}
        and len(native) == len(run["observations"]) == 11,
        "readback and paired archive rosters differ",
    )
    tolerances = specification["comparison_tolerances"]
    pairs = []
    for asset in solidworks["native_files"]:
        name, variant = PurePosixPath(asset["path"]).name, asset["variant"]
        require(
            plan["native_files"][name]["sha256"] == asset["sha256"],
            "readback asset digest differs",
        )
        observation = native[name]
        require(
            observation["face_verified_before_and_after_rebuild"] is True,
            "incomplete native observation",
        )
        before = solidworks_body(observation["before_rebuild"])
        after = solidworks_body(observation["after_rebuild"])
        phase, historical = archived[variant]
        peer = fusion_body(historical)
        pairs.append(
            {
                "variant": variant,
                "solidworks_sha256": asset["sha256"],
                "fusion_sha256": fusion_files[variant],
                "fusion_historical_phase": phase,
                "solidworks_before_rebuild": before,
                "solidworks_after_rebuild": after,
                "fusion_historical_observation": peer,
                "solidworks_rebuild_comparison": compare(before, after, tolerances),
                "reopened_to_fusion_historical": compare(before, peer, tolerances),
                "rebuilt_to_fusion_historical": compare(after, peer, tolerances),
            }
        )
    return {
        "scope": "p04_historical_final_body_observations",
        "capture_revision": REVISION,
        "solidworks_build": SOLIDWORKS_BUILD,
        "solidworks_readback_revision": source,
        "solidworks_readback_receipt_sha256": receipt_digest,
        "solidworks_readback_measurements_sha256": receipt["measurements_sha256"],
        "fusion_measurements_sha256": fusion["measurements"]["sha256"],
        "declared_tolerances": tolerances,
        "topology_count_order": ["faces", "edges", "vertices"],
        "pairs": pairs,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("readback_directory", type=Path)
    parser.add_argument("--receipt-sha256", required=True)
    arguments = parser.parse_args()
    evidence = report(arguments.readback_directory, arguments.receipt_sha256)
    text = json.dumps(evidence, sort_keys=True, indent=2, allow_nan=False)
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
