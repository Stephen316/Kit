# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify the sealed licensed SOLIDWORKS radial-boss discovery prefix offline."""

import argparse
import json
import math
import re
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from Corpus import git
from PairedCaptureIntake import require, sha256
from SolidWorksRadialArchive import inspect_archive

CONTROL_SHA = "d1bbca099ccac1330024619390df3c6b76320a6a6c281a5009578b2fb63e7408"
LOAD = {"document_returned": True, "errors": 0, "warnings": 0}
SAVE = {"returned": True, "errors": 0, "warnings": 0}
BUILD = "34.4.1.1011"
MAX_BYTES = 1024 * 1024


def check_path(path, file=False):
    info = path.lstat()
    match = stat.S_ISREG if file else stat.S_ISDIR
    require(
        match(info.st_mode)
        and not getattr(info, "st_file_attributes", 0)
        & stat.FILE_ATTRIBUTE_REPARSE_POINT,
        f"unexpected linked or nonregular evidence path {path.name}",
    )
    return info


def read_bytes(path, digest, size=None):
    info = check_path(path, file=True)
    require(re.fullmatch(r"[0-9a-f]{64}", digest), f"invalid digest for {path.name}")
    require(0 < info.st_size <= MAX_BYTES, f"invalid evidence size for {path.name}")
    require(
        size is None or info.st_size == size, f"recorded size changed for {path.name}"
    )
    with path.open("rb") as source:
        data = source.read(info.st_size + 1)
    require(
        len(data) == info.st_size and sha256(data) == digest,
        f"digest mismatch for {path.name}",
    )
    return data


def read_record(directory, record):
    name = record["name"]
    return json.loads(
        read_bytes(directory / name, record["sha256"], record["size_bytes"])
    )


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def confirm_controls(phase, names):
    require(
        phase["status"] == "observed"
        and phase["owned_process_exit_observed"] is True
        and phase["application"]["build"] == BUILD
        and [row["file"] for row in phase["observations"]] == names
        and all(row["status"] == "observed" for row in phase["observations"]),
        "unverified licensed process or source roster",
    )
    values = []
    for moment in ("control_before", "control_after"):
        control = phase[moment]
        require(
            control["status"] == "observed"
            and control["open"] == LOAD
            and control["body_count"] == 1
            and positive(control["volume_mm3"]),
            "unhealthy licensed control",
        )
        values.append(control["volume_mm3"])
    return values


def read_capture(directory, expected):
    for path in (*reversed(directory.parents), directory):
        check_path(path)
    attempt = json.loads(read_bytes(directory / "Attempt.json", expected))
    require(
        attempt["schema"] == 1
        and attempt["status"] == "complete"
        and attempt["immutable_sources"] is attempt["fresh_owned_processes"] is True,
        "incomplete licensed capture",
    )
    plan_pin = attempt["plan"]
    require(plan_pin["name"] == "Plan.json", "unexpected native plan")
    plan = read_record(directory, plan_pin)
    require(
        plan["source_revision"] == attempt["source_revision"]
        and re.fullmatch(r"[0-9a-f]{40}", plan["source_revision"])
        and plan["installed_build"] == BUILD
        and plan["original_control_sha256"] == CONTROL_SHA,
        "unverified capture revision, build or control pin",
    )
    read_bytes(directory / "control.SLDPRT", CONTROL_SHA)
    roster = attempt["retained_native_files"]
    sizes = plan["recipe"]["diameters_mm"]
    names = [row["name"] for row in roster]
    require(
        len(sizes) == len(set(sizes)) == 3
        and all(type(size) is int and size > 0 for size in sizes)
        and names == [f"Discovery-D{size}.SLDPRT" for size in sizes]
        and attempt["source_before_reopen"] == attempt["source_after_reopen"] == roster,
        "unstable or unexpected circular discovery source roster",
    )
    phase_pins = attempt["native_phases"]
    require(
        [pin["name"] for pin in phase_pins] == ["Author.json", "Reopen.json"]
        and all(
            pin["exit_code"] == 0 and pin["run_status"] == "observed"
            for pin in phase_pins
        ),
        "unexpected capture phases",
    )
    author, reopened = [read_record(directory, record) for record in phase_pins]
    controls = confirm_controls(author, names) + confirm_controls(reopened, names)
    require(max(controls) - min(controls) <= 0.001, "inconsistent control measurements")
    initial, fresh = author["application"], reopened["application"]
    require(
        type(initial["pid"]) is type(fresh["pid"]) is int
        and initial["pid"] != fresh["pid"]
        and initial["started_utc"] < fresh["started_utc"],
        "discovery files were not reopened in a fresh licensed process",
    )
    return plan, phase_pins, roster, author["observations"], reopened["observations"]


def check_native(parsed, observation, expected_depth):
    dimension, relations, boss, body = (
        observation[key] for key in ("diameter", "relations", "boss", "body")
    )
    require(
        dimension["same_owner"]
        is dimension["targets_circle"]
        is dimension["verified"]
        is True
        and dimension["name"] == parsed["diameter"]["parameter_name"]
        and dimension["owner"]["name"] == parsed["profile"]["name"]
        and dimension["owner"]["id"] == parsed["profile"]["feature_id"]
        and dimension["driven_state"] == 2
        and dimension["type"] == 6
        and dimension["attachments"] == [observation["circle"]],
        "archived circle parameter differs from native driving annotation ownership",
    )
    joined = {row["type"]: row for row in relations}
    require(
        set(joined) == {9, 15}
        and len(relations) == 2
        and all(row["verified"] is True for row in relations)
        and joined[15]["definition_entities"] == [observation["circle"]]
        and {row["native_sketch_owner"] for row in joined[9]["definition_entities"]}
        == {parsed["profile"]["name"], "Origin"},
        "archived center and radial ownership differ from the native observations",
    )
    require(
        math.isclose(
            observation["radius_m"],
            parsed["circle"]["radial_metres"],
            rel_tol=0,
            abs_tol=1e-9,
        )
        and math.isclose(
            dimension["system_value"],
            parsed["diameter"]["diameter_m"],
            rel_tol=0,
            abs_tol=1e-9,
        )
        and observation["support"]["name"] == "Front Plane"
        and observation["units_code"] == 5
        and observation["sketch_regions"] == 1
        and observation["sketch_constraint_status"] == 3
        and boss["end_condition"] == 0
        and boss["both_directions"] is boss["reverse_direction"] is False
        and boss["profile"]["id"] == parsed["profile"]["feature_id"]
        and math.isclose(
            boss["depth_m"], expected_depth / 1000, rel_tol=0, abs_tol=1e-9
        )
        and body["solid_body_count"] == 1
        and positive(body["volume_m3"]),
        "licensed geometry or history differs from the observed discovery scope",
    )


def report(directory, expected):
    plan, phases, roster, author, reopened = read_capture(
        directory.absolute(), expected
    )
    observations = []
    for asset, fresh, source in zip(roster, author, reopened, strict=True):
        require(
            fresh["save"] == SAVE and source["open"] == LOAD,
            f'unhealthy source save or reopen for {asset["name"]}',
        )
        data = read_bytes(
            directory / asset["name"], asset["sha256"], asset["size_bytes"]
        )
        parsed = inspect_archive(data)
        for moment in ("before_rebuild", "after_rebuild"):
            check_native(parsed, source[moment], plan["recipe"]["depth_mm"])
        observations.append({"archive": asset, **parsed})
    return {
        "schema": 1,
        "scope": "licensed_discovery_circular_sketch_prefix",
        "intake_sha256": expected,
        "capture_revision": plan["source_revision"],
        "reader_revision": git(ROOT, "rev-parse", "HEAD").decode("ascii").strip(),
        "application_build": BUILD,
        "native_phases": phases,
        "observations": observations,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--receipt-sha256", required=True)
    options = parser.parse_args()
    try:
        value = report(options.directory, options.receipt_sha256)
        print(
            json.dumps(
                value, ensure_ascii=True, allow_nan=False, indent=2, sort_keys=True
            )
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        TypeError,
        ValueError,
        subprocess.SubprocessError,
    ) as error:
        print(f"radial discovery archive refused: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
