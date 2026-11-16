# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from CutScopeEvidence import ROOT, SPEC_PATH, read_report
from InferenceInputs import checksum, read_input, read_json_input, sha256
from PairedCaptureIntake import GitSnapshot, require
from Records import digest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ApplicationWorkers"))
from AuditFusionPhases import validate_queue
from FusionPhasePlan import (
    SCOPE,
    check_phase_controls,
    check_scope_archives,
    check_scope_report,
    phase_paths,
)
from OutputManifest import output_manifest

# the fixed parked hypothesis has one licensed distinguishing recipe
KScopeGap = "p04-through-all-body-selection"


# the planned licensed study must match the original discovery request
KScopeSpecPin = "298cf204b0e4329186b35d9cc46e36525e3ef2119dc7ddb870e73a5f86289d52"


# the study can admit observations without claiming the saved field meaning
def CheckGridPlan(report, plan):
    grid = report["requested_grid"]
    require(
        report["scope"] == KScopeGap
        and report["status"] == "needs-distinguishing-evidence"
        and "native_grid" not in report
        and grid["specification"] == SPEC_PATH
        and grid["sha256"] == KScopeSpecPin
        and plan["scope"] == SCOPE
        and plan["pins"]["specification"]["sha256"] == KScopeSpecPin,
        "Fusion grid plan does not match the parked scope request",
    )


# exact selectors distinguish controller completions from uploaded report files
def GridInputs(queue, previous_pin):
    validate_queue(queue)
    require(queue.get("scope") == SCOPE, "expected the fixed Fusion scope grid")
    inputs = {
        "grid-queue": f"inference-grid:{digest(queue)}",
        "grid-plan": queue["plan_binding"],
        "grid-previous": f"inference-grid-origin:{checksum(previous_pin)}",
    }
    for phase, parent in queue["jobs"].items():
        stem = f"phase-{phase}"
        inputs[f"{stem}.accepted"] = {"dependency": parent}
        inputs[f"{stem}.dispatch"] = {"dependency": parent, "artifact": "dispatch"}
        for role in phase_paths(queue, phase):
            if phase == "b" or role in (f"{stem}.receipt", f"{stem}.report"):
                inputs[role] = {"dependency": parent, "artifact": role}
    return inputs


# the controller result must belong to the successful attempt for this phase
def GridResult(session, packet, queue, phase):
    parent = queue["jobs"][phase]
    stem = f"phase-{phase}"
    selected = packet["inputs"][f"{stem}.accepted"]
    accepts = packet["dependencies"][parent]
    raw = read_input(session, selected, 1024 * 1024)
    value = json.loads(raw)
    worker = value["receipt"]
    result = value["result"]
    records = result["records"]
    require(
        set(accepts) == {"receipt", "result"}
        and checksum(accepts["receipt"])
        and accepts["result"] == sha256(raw)
        and value["session_version"] == 1
        and worker["receipt_version"] == value["output_artifacts_version"] == 1
        and worker["job_id"] == parent
        and worker["orphan"] is False
        and worker["stop_reason"] is None
        and worker["exit_status"] == 0
        and worker["signal"] is None
        and result["outcome"] == "completed"
        and records["application"] == "fusion"
        and records["phase"] == phase
        and records["scope"] == SCOPE
        and records["installation"] == queue["installation"]
        and records["plan_sha256"] == queue["plan_sha256"]
        and records["native_qualified"] is False,
        "scope grid is not a completed authenticated Fusion supervisor attempt",
    )
    manifest = output_manifest(value["output_artifacts"], paths=False)
    require(
        result["artifacts"] == manifest
        and set(manifest) == set(phase_paths(queue, phase)) | {"dispatch"},
        "scope grid result has a different accepted artifact roster",
    )
    return manifest, records


# staged bytes must match the accepted phase manifest even after spool cleanup
def GridArtifact(session, inputs, manifest, role, key, limit=4 * 1024 * 1024):
    raw = read_input(session, inputs[role], limit)
    require(
        manifest[key] == {"sha256": sha256(raw), "size_bytes": len(raw)},
        "scope grid artifact differs from its accepted manifest",
    )
    return raw


# both ends of each phase must come from the same healthy pinned installation
def GridPhase(session, packet, queue, plan, phase, staged):
    stem = f"phase-{phase}"
    inputs = packet["inputs"]
    manifest, records = GridResult(session, packet, queue, phase)
    dispatch = json.loads(
        GridArtifact(session, inputs, manifest, f"{stem}.dispatch", "dispatch")
    )
    proof = dispatch["proof"]
    receipt = GridArtifact(
        session, inputs, manifest, f"{stem}.receipt", f"{stem}.receipt"
    )
    raw = GridArtifact(session, inputs, manifest, f"{stem}.report", f"{stem}.report")
    report = json.loads(raw)
    check_scope_report(json.loads(receipt), report, raw, queue["plan_sha256"], phase)
    check_scope_archives(report, manifest, phase)
    check_phase_controls(report, plan)
    require(
        dispatch["version"] == 1
        and dispatch["provider"] == "autodesk.fusion.addin"
        and dispatch["status"] == "completed"
        and dispatch["source_revision"]
        == report["source_revision"]
        == queue["source_revision"]
        and dispatch["installation"] == queue["installation"]
        and dispatch["host"] == proof["host"] == records["host"]
        and dispatch["host"]["pid"] == report["process"]["pid"]
        and proof["claim"] == "unqualified_application_observation"
        and proof["phase"] == phase
        and proof["scope"] == SCOPE
        and proof["plan_sha256"] == queue["plan_sha256"]
        and proof["fusion_version"]
        == report["application_build"]
        == records["fusion_version"]
        and "fixture_only" not in proof
        and "fixture_only" not in report,
        "scope grid dispatch identity differs or belongs to a disposable fixture",
    )
    expected = phase_paths(queue, phase)
    files = output_manifest(dispatch["files"])
    require(
        files
        == {role: {**manifest[role], "path": path} for role, path in expected.items()},
        "scope grid dispatch does not pin the accepted phase artifacts",
    )
    if phase == "b":
        (staged / "receipt.json").write_bytes(receipt)
        (staged / "report.json").write_bytes(raw)
        for role, path in expected.items():
            if path.endswith(".f3d"):
                data = GridArtifact(
                    session, inputs, manifest, role, role, 256 * 1024 * 1024
                )
                (staged / Path(path).name).write_bytes(data)
    return report, sha256(raw)


# archived measurements cannot resolve the storage hypothesis by themselves
def ObserveGrid(session, packet, report):
    inputs = packet["inputs"]
    pin = packet["job"]["options"]["grid_from_receipt"]
    queue = read_json_input(session, inputs["grid-queue"])
    selectors = GridInputs(queue, pin)
    require(
        set(inputs) == set(selectors) | {"plan"}
        and all(
            inputs[role]["binding"] == selector for role, selector in selectors.items()
        )
        and inputs["grid-queue"]["sha256"] == digest(queue)
        and inputs["grid-plan"]["sha256"] == queue["plan_sha256"],
        "scope grid requires exact accepted dependency and plan selectors",
    )
    previous = read_json_input(session, inputs["grid-previous"])
    require(
        inputs["grid-previous"]["sha256"] == pin
        and previous["receipt_version"] == 1
        and previous["outcome"] == "waiting_evidence"
        and previous["job_id"]
        == packet["job"]["id"]
        == "inference:" + digest(KScopeGap)
        and previous["generation"] < packet["generation"]
        and previous["fingerprint"] == digest(previous["snapshot"])
        and previous["snapshot"]["inputs"]["plan"]
        == {key: inputs["plan"][key] for key in ("binding", "sha256")},
        "scope grid no longer binds the parked assessment plan and attempt",
    )
    plan = read_json_input(session, inputs["grid-plan"])
    CheckGridPlan(report, plan)
    with TemporaryDirectory(prefix="kit-inference-grid-") as scratch:
        staged = Path(scratch)
        first, first_pin = GridPhase(session, packet, queue, plan, "a", staged)
        second, second_pin = GridPhase(session, packet, queue, plan, "b", staged)
        require(
            first.get("previous_process") is None
            and first.get("previous_phase_report_sha256") is None
            and second["previous_process"] == first["process"]
            and second["previous_phase_report_sha256"] == first_pin
            and second["process"]["pid"] != first["process"]["pid"]
            and second["process"]["start_unix_seconds"] > first["ended_unix_seconds"]
            and second["application_build"] == first["application_build"],
            "scope grid measurements do not establish the exact fresh process pair",
        )
        native, _ = read_report(
            staged / "report.json", second_pin, "fusion", GitSnapshot(ROOT)
        )
    return {
        "fusion": native,
        "plan_sha256": queue["plan_sha256"],
        "controller_dependencies": {
            job: packet["dependencies"][job] for job in queue["jobs"].values()
        },
        "previous_report_sha256": first_pin,
        "qualification": False,
    }
