# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from InferenceArchives import archive_cases, archive_gaps
from InferenceRunner import FIELD_KIND, RESCAN_KIND, result_schema
from InferenceSchedule import build_schedule
from PairedCaptureIntake import require
from Records import canonical, digest

AUTOMATION = Path(__file__).resolve().parent
ROOT = AUTOMATION.parents[1]


def invoke(script, *arguments, timeout=90):
    process = subprocess.run(
        [sys.executable, "-B", str(AUTOMATION / script), *map(str, arguments)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if process.returncode:
        raise ValueError(
            f"{script} exited with {process.returncode}: {process.stderr[-4096:]}"
        )
    return process.stdout


class GateStore:
    def __init__(self, directory):
        self.directory = directory
        self.store = directory / "Store"
        self.controller("init")
        schema = self.write("Schema.json", result_schema())
        entry = {
            "pool": "inference",
            "argv": [
                sys.executable,
                "-B",
                str(AUTOMATION / "InferenceRunner.py"),
                "{session}",
            ],
            "result_schema": str(schema),
            "initial_peak_memory_mib": 128,
            "max_memory_mib": 768,
        }
        registry = self.write(
            "Registry.json",
            {
                "runners": {FIELD_KIND: entry, RESCAN_KIND: entry},
            },
        )
        self.config = self.write(
            "Supervisor.json",
            {
                "state": str(directory / "SupervisorState"),
                "controller": {"adapter": "a03", "store": str(self.store)},
                "registry": str(registry),
                "worker": "supervisor:inference-archive",
                "pools": {"inference": {"max_sessions": 2}},
                "stop_grace_seconds": 1,
                "poll_seconds": 0.1,
                "reserved_cpus": 0,
                "reserved_memory_mib": 0,
                "adaptive_limits": False,
            },
        )

    def write(self, name, record):
        path = self.directory / name
        path.write_text(canonical(record) + "\n", encoding="utf-8")
        return path

    def controller(self, *arguments):
        return json.loads(invoke("Controller.py", "--store", self.store, *arguments))

    def bind(self, name, content):
        path = self.directory / "BindInput"
        path.write_bytes(content)
        self.controller("bind", name, path)
        return name

    def schedule(self, request):
        batch = build_schedule(request)
        self.controller("schedule", self.write("Schedule.json", batch))
        return batch["jobs"]

    def run(self):
        invoke(
            "Supervisor.py",
            "--config",
            self.config,
            "run",
            "--idle-seconds",
            "3",
            "--max-seconds",
            "120",
            timeout=150,
        )
        return {job["id"]: job for job in self.controller("status")["jobs"]}

    def result(self, job, statuses):
        status = statuses[job["id"]]
        require(
            status["state"] == "completed", f"inference job did not complete: {status}"
        )
        value = self.controller("artifact", status["result"])
        return json.loads(Path(value["path"]).read_bytes())["result"]["records"]


def stage(gate, plan, streams, archives):
    scope = plan["scope"]
    return {
        "inference_version": 1,
        "scope": scope,
        "family": "rectangular-history",
        "rule_version": "archive-field-search@1",
        "tool_version": "inference-archive-gate@1",
        "plan_input": gate.bind(scope + ":plan", canonical(plan).encode("utf-8")),
        "stream_inputs": {
            role: gate.bind(role, content) for role, content in sorted(streams.items())
        },
        "archives": {
            pin: {"format": source_format, "binding": gate.bind(pin, content)}
            for pin, (source_format, content) in sorted(archives.items())
        },
        "distinguishing_evidence": [
            "direction-negative",
            "depth-edit",
            "width-edit",
            "height-edit",
        ],
        "depends_on": [],
    }


def verify_case(gate, jobs, statuses):
    assessment = gate.result(jobs[0], statuses)
    search = assessment["assessment"]
    sources = assessment["provenance"]["inputs"]
    is_solidworks = assessment["scope"].endswith(".solidworks")
    candidate = [
        row
        for row in search["hypotheses"]
        if row["encoding"]["type"] == "f64"
        and row["encoding"]["endian"] == "little"
        and row["encoding"]["unit"] == ("m" if is_solidworks else "cm")
        and all(
            item["offset"] == sources[item["sample"]]["typed_scalar_offset"]
            for item in row["discovery"]
        )
    ]
    require(len(candidate) == 1, "bounded search failed to locate the owned depth")
    row = candidate[0]
    require(
        search["discrimination"]["target_pair"]
        and not search["discrimination"]["unresolved_controls"]
        and not search["holdout"],
        "the archived grid lost an independent control or admitted a holdout",
    )
    require(
        row["confidence"] == ("refuted" if is_solidworks else "partial")
        and len(row["challenges"]) == 1
        and (row["challenges"][0]["status"] == "mismatch") == is_solidworks,
        "the negative direction control did not distinguish scalar ownership",
    )
    rescans = [gate.result(job, statuses) for job in jobs[1:]]
    require(
        sorted(item["source_sha256"] for item in rescans) == assessment["source_sha256"]
        and all(item["assessment_sha256"] == digest(assessment) for item in rescans),
        "affected archive census differs from the inference scope",
    )
    return {
        "scope": assessment["scope"],
        "discovery_sha256": search["discovery_sha256"],
        "candidate": row,
        "counterexamples": search["counterexamples"],
        "rescanned": assessment["source_sha256"],
    }


def check(directory):
    gate = GateStore(directory)
    requests = [stage(gate, *case) for case in archive_cases()]
    require(len(requests) == 2, "inference requires the paired archive scopes")
    schedules = [gate.schedule(request) for request in requests]
    first = gate.run()
    results = [verify_case(gate, jobs, first) for jobs in schedules]
    for request in requests:
        gate.schedule(request)
    unchanged = gate.run()
    require(first.keys() == unchanged.keys(), "replay produced a new job roster")
    require(
        all(first[job]["receipt"] == unchanged[job]["receipt"] for job in first),
        "unchanged discovery or counterexamples were retried",
    )
    gate.schedule({**requests[0], "rule_version": "archive-field-search@2"})
    changed = gate.run()
    rerun = {job for job in first if first[job]["receipt"] != changed[job]["receipt"]}
    require(
        rerun == {job["id"] for job in schedules[0]},
        "rule change caused a rescan beyond the affected scope",
    )
    verify_case(gate, schedules[0], changed)
    gaps = archive_gaps()
    require(
        {(gap["scope"], gap["status"]) for gap in gaps}
        == {
            ("p04-cut-termination", "refuted"),
            ("p04-through-all-body-selection", "needs-distinguishing-evidence"),
        },
        "paired Cut hypotheses lost their controls or unresolved policy",
    )
    return {
        "inference_version": 1,
        "cases": results,
        "shared_gaps": gaps,
        "unchanged_attempts": len(unchanged),
        "affected_jobs": sorted(rerun),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Verify A07 against pinned native archive controls"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        with TemporaryDirectory(prefix="kit-inference-") as directory:
            result = check(Path(directory))
        with args.output.open("x", encoding="utf-8") as output:
            output.write(canonical(result) + "\n")
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        subprocess.SubprocessError,
    ) as error:
        parser.exit(1, f"inference archive verification failed: {error}\n")


if __name__ == "__main__":
    main()
