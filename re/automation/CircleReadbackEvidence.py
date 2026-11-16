# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify the saved SOLIDWORKS P02 archive observations without CAD."""

import argparse
import json
import math
import re
import stat
import subprocess
import sys
from pathlib import Path

from Corpus import git
from PairedCaptureIntake import GitSnapshot, require, sha256

CAPTURES = "re/automation/PairedCaptures"
AUTHORING = f"{CAPTURES}/SolidWorksAuthoring"
P02 = f"{CAPTURES}/P02/solidworks-4a9e35f34a39"
CAPTURE_RECEIPT = "f96892773ceadb4fa608395af20bb1dcee8690d7bb100865cc16c0920ec60b2a"
CONTROL = "d1bbca099ccac1330024619390df3c6b76320a6a6c281a5009578b2fb63e7408"
SPEC = "3c93e024f9fbdda50e610bda3b363bf30e8e7cdc914ef0728087befe129951bf"
BUILD = "34.4.1.1011"
LOAD = {"document_returned": True, "errors": 0, "warnings": 0}
ZERO = (0, 0, 0)
SOURCE_PATHS = {
    "specification": "re/automation/PairSpecs.json",
    "launcher": f"{AUTHORING}/ReadP04SolidWorks.ps1",
    "collector": f"{AUTHORING}/P04Readback.cs",
    "circle_collector": f"{AUTHORING}/P02Readback.cs",
    "control": "re/solidworks/examples/.SLDPRT/example.SLDPRT",
}


# rebuilt reports must remain isolated from links and large private files
def plain(path, file=False):
    info = path.lstat()
    check = stat.S_ISREG if file else stat.S_ISDIR
    require(
        check(info.st_mode)
        and not getattr(info, "st_file_attributes", 0)
        & stat.FILE_ATTRIBUTE_REPARSE_POINT,
        f"readback path is not a plain {'file' if file else 'directory'}: {path.name}",
    )
    return info


# byte digests precede JSON interpretation and retain the exact native observation chain
def read_record(path, expected):
    require(re.fullmatch(r"[0-9a-f]{64}", expected), f"invalid digest for {path.name}")
    size = plain(path, file=True).st_size
    require(0 < size <= 1024 * 1024, f"invalid size for {path.name}")
    with path.open("rb") as handle:
        data = handle.read(size + 1)
    require(
        len(data) == size and sha256(data) == expected,
        f"digest mismatch for {path.name}",
    )
    return GitSnapshot.parse_document(data, path.name)


# source proof verifies the complete recorded Git identity, digest, length and relative path
def source_pin(snapshot, revision, path, pin, expected=None):
    data = snapshot.blob(revision, path)
    digest = sha256(data)
    require(
        pin
        == {
            "path": path,
            "git_blob": snapshot.tree(revision)[path],
            "sha256": digest,
            "size_bytes": len(data),
        }
        and (expected is None or digest == expected),
        f"source pin differs for {path}",
    )
    return data


# the native collector can open only the five audited archive variants and the pinned control
def pinned_capture(snapshot, revision, plan):
    require(
        plan["recipe"] == "P02" and set(plan["existing_captures"]) == {"P02"},
        "not a P02 plan",
    )
    for role, path in SOURCE_PATHS.items():
        source_pin(
            snapshot,
            revision,
            path,
            plan[role],
            {"control": CONTROL, "specification": SPEC}.get(role),
        )
    for name in ("executable", "interop", "constants"):
        require(
            re.fullmatch(r"[0-9a-f]{64}", plan[f"installed_{name}_sha256"]),
            f"invalid installed {name} digest",
        )
    capture = plan["existing_captures"]["P02"]
    receipt_bytes = source_pin(
        snapshot, revision, f"{P02}/receipt.json", capture["receipt"], CAPTURE_RECEIPT
    )
    receipt = snapshot.parse_document(receipt_bytes, "P02 capture receipt")
    measurement_bytes = source_pin(
        snapshot,
        revision,
        f"{P02}/measurements.json",
        capture["measurements"],
        receipt["measurement_receipt_sha256"],
    )
    history = snapshot.parse_document(measurement_bytes, "P02 capture measurements")
    roster = receipt["native_files"]
    names = {asset["file"] for asset in roster}
    require(
        receipt["recipe_id"] == history["recipe_id"] == "P02"
        and history["specifications_sha256"] == SPEC
        and receipt["errors"] == 0
        and len(names) == len(roster) == 5
        and names
        == set(plan["native_files"])
        == set(history["observations"]["reopened_files"]),
        "P02 readback and capture rosters differ",
    )
    for asset in roster:
        name = asset["file"]
        data = source_pin(
            snapshot,
            revision,
            f"{P02}/{name}",
            plan["native_files"][name],
            asset["sha256"],
        )
        require(
            len(data) == asset["size_bytes"]
            and asset["save_errors"] == asset["save_warnings"] == 0,
            f"P02 capture did not save cleanly: {name}",
        )
    return roster, history["observations"]


# numeric inputs must be finite application measurements in the declared native units
def near(value, expected, tolerance):
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and abs(value - expected) <= tolerance
    )


# point and transformation witnesses require all coordinates rather than matching a subset
def vector_near(value, expected, tolerance=1e-9):
    return len(value) == len(expected) and all(
        near(item, prior, tolerance)
        for item, prior in zip(value, expected, strict=True)
    )


# identity joins use native owner and local ID, because identical IDs can occur in separate owners
def point_identity(row, owner, same_sketch):
    require(
        row["kind"] == "sketch_point"
        and row["native_sketch_owner"] == owner
        and row["same_sketch"] is same_sketch
        and row["native_sketch_available"] is True
        and len(row["id"]) == 2
        and all(type(value) is int for value in row["id"])
        and vector_near(row["local_m"], ZERO),
        f"native P02 point identity is not owned by {owner}",
    )
    return owner, tuple(row["id"])


# the sketch's owned circle must receive both the displayed dimension and solver operand
def circle_bindings(row):
    circle, dimension = row["circle"], row["dimension"]
    require(
        circle["kind"] == "sketch_segment"
        and circle["type"] == 1
        and circle["same_sketch"] is True
        and len(circle["id"]) == 2
        and all(type(value) is int for value in circle["id"])
        and dimension["name"] == "diameter_mm"
        and dimension["full_name"].split("@")[:2] == ["diameter_mm", "CircleSketch"]
        and dimension["type"] == 6
        and dimension["driven_state"] == 2
        and dimension["owner"] == row["feature"]
        and dimension["same_owner"] is True
        and dimension["dangling"] is False
        and dimension["attachment_count"] == 1
        and dimension["attachment_types"] == [10]
        and dimension["attachments"] == [circle]
        and dimension["attachment_status"] == "observed_slots"
        and dimension["targets_circle"] is dimension["verified"] is True,
        "the owned P02 driving diameter does not target the circle",
    )
    center = point_identity(row["center_point"], "CircleSketch", True)
    origin = point_identity(row["origin_point"], "Origin", False)
    relations = {item["type"]: item for item in row["relations"]}
    require(
        set(relations) == {9, 15}
        and len(row["relations"]) == 2
        and all(
            item["verified"] is True and "diagnostic" not in item
            for item in relations.values()
        )
        and relations[15]["entities"]
        == relations[15]["definition_entities"]
        == [circle],
        "native P02 diameter relation does not bind the circle",
    )
    origin_pair = relations[9]["definition_entities"]
    require(
        len(origin_pair) == 2
        and {
            point_identity(
                item,
                item["native_sketch_owner"],
                item["native_sketch_owner"] == "CircleSketch",
            )
            for item in origin_pair
        }
        == {center, origin},
        "native P02 coincidence does not bind the center to the document origin",
    )


# each observed state is checked against the saved capture's independent native measurements
def verify_state(row, prior):
    (before_sketch,) = prior["sketches"]
    (before_circle,) = before_sketch["entities"]
    diameter = row["dimension"]["system_value"]
    radius = row["radius_m"]
    area = row["section_area_m2"]
    require(
        row["verified"] is row["profile_verified"] is True
        and row["feature"]["name"] == "CircleSketch"
        and row["feature"]["type"] == "ProfileFeature"
        and row["feature"]["suppressed"] is False
        and row["feature_error"] == 0
        and row["feature_warning"] is False
        and row["constraint_status"] == 3
        and row["region_count"] == 1
        and row["solid_body_count"] == prior["body_count"] == 0
        and row["units_code"] == prior["units_code"]
        and row["support"]["type"] == "RefPlane"
        and row["support"]["suppressed"] is False
        and row["support"]["name"] == before_sketch["support_name"]
        and row["support_type"] == before_sketch["support_type"]
        and vector_near(
            row["model_to_sketch_transform"], before_sketch["model_to_sketch_transform"]
        )
        and vector_near(row["center_world_m"], ZERO)
        and vector_near(row["section_center_world_m"], ZERO)
        and near(radius, before_circle["radius_mm"] / 1000, 1e-9)
        and near(diameter, 2 * radius, 1e-9)
        and near(area, before_sketch["section_area_mm2"] / 1e6, 1e-12)
        and near(area, math.pi * radius**2, 1e-12),
        "native P02 geometry, datum, units or feature health differs from capture",
    )
    circle_bindings(row)
    return {
        "diameter_mm": diameter * 1000,
        "radius_mm": radius * 1000,
        "area_mm2": area * 1e6,
        "support_name": row["support"]["name"],
        "units_code": row["units_code"],
        "solid_body_count": 0,
    }


# a successful session requires the known solid before and after the bounded readback
def verify_controls(run, historical):
    for moment in ("before", "after"):
        control, prior = (
            run[f"control_{moment}"],
            historical[f"healthy_control_{moment}"],
        )
        require(
            control["status"] == "observed"
            and control["open"] == LOAD
            and control["body_count"] == prior["body_count"] == 1
            and near(control["volume_mm3"], prior["volume_mm3"], 0.001)
            and vector_near(
                control["center_of_mass_m"],
                [axis / 1000 for axis in prior["center_of_mass_mm"]],
            ),
            f"the native {moment} control differs from the pinned health observation",
        )


# check the full immutable chain and return only observations suitable for coordinated intake
def verify(root, directory, receipt_digest, expected_revision):
    require(
        re.fullmatch(r"[0-9a-f]{40}", expected_revision), "expected full source commit"
    )
    revision = (
        git(root, "rev-parse", "--verify", expected_revision + "^{commit}")
        .decode("ascii")
        .strip()
    )
    require(revision == expected_revision, "expected revision is not a commit")
    directory = directory.absolute()
    for parent in (*reversed(directory.parents), directory):
        plain(parent)
    receipt = read_record(directory / "receipt.json", receipt_digest)
    plan = read_record(directory / "plan.json", receipt["plan_sha256"])
    measured = read_record(
        directory / "measurements.json", receipt["measurements_sha256"]
    )
    require(
        receipt["schema"] == measured["schema"] == 1
        and receipt["status"] == "observed"
        and receipt["observed_files"] == receipt["circle_bindings_verified"] == 5
        and measured["plan_sha256"] == receipt["plan_sha256"]
        and measured["claim"] == "supplemental_native_observation"
        and measured["source_bytes_verified_after_readback"] is True
        and plan["source_revision"] == revision,
        "receipt does not bind the observed P02 plan and source revision",
    )
    roster, historical = pinned_capture(GitSnapshot(root), revision, plan)
    run = measured["run"]
    require(
        run["status"] == "observed"
        and run["owned_process_exit_observed"] is True
        and run["application"]["build"] == BUILD
        and run["application"]["revision"] == "34.4.1"
        and type(run["application"]["pid"]) is int
        and run["application"]["pid"] > 0
        and isinstance(run["application"]["started_utc"], str)
        and run["application"]["started_utc"].endswith("Z"),
        "the observed SOLIDWORKS process or build did not pass",
    )
    verify_controls(run, historical)
    observations = {row["file"]: row for row in run["observations"]}
    require(
        len(run["observations"]) == len(observations) == 5
        and observations.keys() == {asset["file"] for asset in roster},
        "native observations do not cover the exact capture roster",
    )
    results = []
    for asset in roster:
        name = asset["file"]
        row = observations[name]
        require(
            row["status"] == "observed"
            and row["open"] == LOAD
            and row["circle_verified_before_and_after_rebuild"] is True,
            f"native P02 open or rebuild is incomplete: {name}",
        )
        prior = historical["reopened_files"][name]
        results.append(
            {
                "file": name,
                "source_sha256": asset["sha256"],
                "open": row["open"],
                "before_rebuild": verify_state(row["before_rebuild"], prior),
                "after_rebuild": verify_state(row["after_rebuild"], prior),
            }
        )
    return {
        "schema": 1,
        "status": "verified_observations",
        "scope": "solidworks_p02_circle_bindings",
        "source_revision": revision,
        "application_build": BUILD,
        "receipt_sha256": receipt_digest,
        "measurements_sha256": receipt["measurements_sha256"],
        "plan_sha256": receipt["plan_sha256"],
        "observations": results,
    }


# CLI accepts an independently recorded digest and exact licensed collector revision
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("readback_directory", type=Path)
    parser.add_argument("--receipt-sha256", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    args = parser.parse_args()
    try:
        observation = verify(
            args.root,
            args.readback_directory,
            args.receipt_sha256,
            args.source_revision,
        )
        print(json.dumps(observation, allow_nan=False, indent=2, sort_keys=True))
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        TypeError,
        ValueError,
        subprocess.SubprocessError,
    ) as error:
        print(f"SOLIDWORKS P02 readback verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
