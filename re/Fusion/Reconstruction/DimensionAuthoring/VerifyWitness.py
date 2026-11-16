# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import math
import re
import subprocess
from pathlib import Path

from ProbeAcceptance import (
    MAX_ARCHIVE_BYTES,
    PINS,
    SCOPE,
    CANDIDATES,
    archive_pin,
    candidate_inputs,
    committed_pin,
    read_file,
    read_pin,
    require,
)
from WitnessMeasurements import verify_measurements


def parse_sha(value):
    require(
        isinstance(value, str) and re.fullmatch("[a-f0-9]{64}", value),
        "Expected an exact SHA-256",
    )
    return value


def unique_object(pairs):
    result = dict(pairs)
    require(len(result) == len(pairs), "Unexpected duplicate JSON fields")
    return result


def read_object(path, expected=None):
    raw = read_file(path)
    checksum = archive_pin(raw)["sha256"]
    if expected is not None:
        require(
            checksum == parse_sha(expected), f"Pinned metadata changed: {path.name}"
        )
    value = json.loads(raw, object_pairs_hook=unique_object)
    require(isinstance(value, dict), "Witness metadata must be a JSON object")
    return value, checksum


def direct_directory(path):
    require(
        path.is_dir()
        and not path.is_symlink()
        and path.absolute() == path.resolve(strict=True),
        "Witness directory must be a direct filesystem path",
    )
    return path.absolute()


def read_plan(root, checksum):
    plan, _ = read_object(root / "plan.json", checksum)
    revision = plan["source_revision"]
    require(
        type(plan["schema"]) is int
        and plan["schema"] == 1
        and plan["scope"] == SCOPE
        and plan["candidate_kind"] in CANDIDATES
        and type(plan["prepared_unix_seconds"]) is int
        and plan["prepared_unix_seconds"] > 0
        and isinstance(revision, str)
        and re.fullmatch("[a-f0-9]{40}", revision)
        and set(plan["pins"]) == set(PINS),
        "Invalid prepared witness plan",
    )
    require(
        plan["pins"]
        == {name: committed_pin(revision, path) for name, path in PINS.items()},
        "Witness helpers or control differ from the declared Git source",
    )
    _, _, candidate = candidate_inputs(
        direct_directory(root / "inputs"), plan["candidate_kind"]
    )
    require(
        candidate == plan["candidate"],
        "Retained candidate archive or generation proof changed",
    )
    return plan


def read_phase(root, phase, pin, plan, plan_hash, build):
    directory = direct_directory(root / f"phase-{phase}")
    receipt, _ = read_object(directory / "receipt.json", pin)
    report, report_hash = read_object(
        directory / "measurements.json", receipt["measurements_sha256"]
    )
    require(
        set(receipt)
        == {"schema", "scope", "phase", "status", "measurements_sha256", "plan_sha256"}
        and all(
            type(value["schema"]) is int
            and value["schema"] == 1
            and value["scope"] == SCOPE
            and value["phase"] == phase
            and value["status"] == "complete"
            and value["plan_sha256"] == plan_hash
            for value in (receipt, report)
        )
        and all(
            report[key] == plan[key]
            for key in ("candidate_kind", "source_revision", "candidate", "pins")
        )
        and report["claim"] == "licensed research candidate witness"
        and report["errors"] == []
        and report["fusion_version"] == build,
        f"Phase {phase.upper()} does not bind the successful plan, report and Fusion build",
    )
    return report, report_hash


def check_process(report, prepared):
    process = report["process"]
    started = report["started_unix_seconds"]
    ended = report["ended_unix_seconds"]
    require(
        set(process) == {"pid", "start_unix_seconds"}
        and type(process["pid"]) is int
        and process["pid"] > 1
        and type(process["start_unix_seconds"]) is int
        and all(
            type(value) in (int, float) and math.isfinite(value)
            for value in (started, ended)
        )
        and prepared <= process["start_unix_seconds"] <= started < ended,
        "Invalid native process identity or measurement interval",
    )
    return process


def verify(root, plan_hash, phase_a_hash, phase_b_hash, build):
    require(
        re.fullmatch(r"[0-9]+(?:\.[0-9]+){2}", build), "Expected an exact Fusion build"
    )
    root = direct_directory(root)
    plan = read_plan(root, plan_hash)
    first, first_hash = read_phase(root, "a", phase_a_hash, plan, plan_hash, build)
    second, second_hash = read_phase(root, "b", phase_b_hash, plan, plan_hash, build)
    a_process = check_process(first, plan["prepared_unix_seconds"])
    b_process = check_process(second, plan["prepared_unix_seconds"])
    require(
        first_hash == second["previous_measurements_sha256"]
        and a_process["pid"] != b_process["pid"]
        and a_process["start_unix_seconds"] < b_process["start_unix_seconds"]
        and int(first["ended_unix_seconds"]) <= b_process["start_unix_seconds"]
        and first["ended_unix_seconds"] <= second["started_unix_seconds"],
        "Phase B does not bind the exact prior measurement and a fresh process",
    )
    restored = first["restored_archive"]
    require(restored["file"] == "restored.f3d", "Unexpected restored archive filename")
    read_pin(root / "phase-a" / "restored.f3d", restored, MAX_ARCHIVE_BYTES)
    observation = verify_measurements(plan, first, second, restored)
    return {
        "status": "verified_rectangle_witness",
        "scope": SCOPE,
        "candidate_kind": plan["candidate_kind"],
        "source_revision": plan["source_revision"],
        "codec_revision": plan["candidate"]["codec_revision"],
        "fusion_version": build,
        "plan_sha256": plan_hash,
        "phase_a_receipt_sha256": phase_a_hash,
        "phase_a_measurements_sha256": first_hash,
        "phase_a_process": a_process,
        "phase_b_receipt_sha256": phase_b_hash,
        "phase_b_measurements_sha256": second_hash,
        "phase_b_process": b_process,
        "input_archive_sha256": plan["candidate"]["input"]["sha256"],
        "restored_archive_sha256": restored["sha256"],
        **observation,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Verify one retained Fusion rectangle witness offline"
    )
    parser.add_argument("--witness", type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--phase-a-receipt-sha256", required=True)
    parser.add_argument("--phase-b-receipt-sha256", required=True)
    parser.add_argument("--fusion-version", required=True)
    args = parser.parse_args()
    try:
        result = verify(
            args.witness,
            args.plan_sha256,
            args.phase_a_receipt_sha256,
            args.phase_b_receipt_sha256,
            args.fusion_version,
        )
    except (
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        IndexError,
        TypeError,
        subprocess.CalledProcessError,
    ) as error:
        parser.exit(1, f"Fusion rectangle witness refused: {error}\n")
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
