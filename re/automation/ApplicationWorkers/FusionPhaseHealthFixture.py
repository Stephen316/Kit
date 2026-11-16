# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import time
from pathlib import Path

from ApplicationProtocol import (
    HostQueue,
    configuration,
    file_bytes,
    pin,
    record,
    sha256,
    write_record,
)
from FusionPhasePlan import phase_paths, phase_process


# native control refusals need a completed transport response from a disposable peer
def phase_output(host, value, work, plan, fault):
    phase = work / "phase-a"
    phase.mkdir(mode=0o700)
    roster = phase_paths(plan, "a")
    captures = {}
    for recipe in plan["recipes"]:
        relative = roster[f"phase-a.{recipe}"]
        archive = work / relative
        archive.write_bytes(b"disposable phase proof fixture")
        saved = pin(archive, relative)
        captures[recipe] = {
            "save_a": {
                "file": archive.name,
                "sha256": saved["sha256"],
                "size_bytes": saved["size_bytes"],
            }
        }
    plan_hash = value["body"]["plan_sha256"]
    receipt = {
        "schema": 1,
        "phase": "a",
        "status": "complete",
        "plan_sha256": plan_hash,
    }
    control = {"compute_all_return": True, "native_input": plan["pins"]["control"]}
    report = {
        **receipt,
        "source_revision": host.config["source_revision"],
        "fixture_only": True,
        "process": phase_process(host.host),
        "fusion_version": "disposable fixture",
        "pins": plan["pins"],
        "healthy_control_before": control,
        "healthy_control_after": {**control, "compute_all_return": fault != "after"},
        "errors": [],
        "captures": captures,
        "ended_unix_seconds": time.time(),
    }
    write_record(phase / "measurements.json", report)
    receipt["measurements_sha256"] = sha256(file_bytes(phase / "measurements.json"))
    write_record(phase / "receipt.json", receipt)
    proof = {
        "claim": "unqualified_application_observation",
        "fixture_only": True,
        "phase": "a",
        "plan_sha256": plan_hash,
        "host": host.host,
        "fusion_version": report["fusion_version"],
        "restart_handoff": host.restart_handoff(value, plan_hash),
    }
    return (
        "completed",
        "disposable phase fixture",
        proof,
        {role: pin(work / relative, relative) for role, relative in roster.items()},
    )


# exercising the real queue keeps copied bytes and the controller result separate
def run_host(config, fault):
    host = HostQueue(config)

    # separate readiness and phase replies isolate the after control as the failure
    def action(value, work):
        if value["operation"] == "probe":
            return (
                "completed",
                "disposable challenge",
                {
                    "control": "healthy",
                    "host": host.host,
                    "plan_sha256": value["body"]["plan_sha256"],
                    "documents_after": 0,
                    "measured_at": time.time(),
                },
                {},
            )
        return phase_output(host, value, work, record(work / "plan.json"), fault)

    write_record(host.root / "ready.json", {"host": host.host})
    try:
        while not (host.root / "stop-fixture").exists():
            request = host.next_path()
            if request is None:
                time.sleep(0.025)
                continue
            host.perform(request, action)
    finally:
        host.close()


# the hosted process receives a fixed scenario without importing any cad module
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fault", choices=("after", "fixture"))
    parser.add_argument("--installation", type=Path, required=True)
    args = parser.parse_args()
    run_host(configuration(args.installation), args.fault)


if __name__ == "__main__":
    main()
