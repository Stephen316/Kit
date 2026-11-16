# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from pathlib import Path

from InferenceGrid.Evidence import KScopeGap, KScopeSpecPin
from InferenceInputs import sha256
from PairedCaptureIntake import require
from Records import canonical

from FusionPhasePlan import SCOPE, phase_identity, phase_paths
from QueueFusionPhases import phase_jobs


# a current application queue can be attached before either acceptance exists
def QueueFixture(gate, report):
    installation = {
        "installation": "fusion:grid-fixture",
        "source_revision": report["requested_grid"]["revision"],
    }
    plan = {
        "scope": SCOPE,
        "source_revision": installation["source_revision"],
        "pins": {"specification": {"sha256": KScopeSpecPin}},
    }
    raw = canonical(plan).encode("utf-8")
    plan_pin = sha256(raw)
    resource = "application:grid-fixture"
    kind = "fixture.scope-grid"
    binding, jobs = phase_jobs(
        installation, kind, resource, "inference-grid-fixture", plan, plan_pin
    )
    gate.bind(binding, raw)
    gate.controller("resource", resource, "--capacity", "1")
    gate.controller("pool", "grid-fixture", "--kind", kind)
    gate.controller("submit-batch", gate.write("GridJobs.json", {"jobs": jobs}))
    return {
        **installation,
        **phase_identity(plan),
        "resource": resource,
        "jobs": {item["options"]["phase"]: item["id"] for item in jobs},
        "plan_sha256": plan_pin,
        "plan_binding": binding,
    }


# failed admission must report the gate that withheld acceptance
def RefuseScope(call, text):
    try:
        call()
    except ValueError as error:
        require(
            text in str(error),
            f"scope grid was refused for an unexpected reason: {error}",
        )
    else:
        raise ValueError("scope grid unexpectedly accepted an invalid input")


# accepted storage bytes alone cannot elevate a disposable result to native evidence
def FinishFixture(gate, queue, phase):
    folder = gate.directory / f"GridFixture-{phase}"
    work = folder / "work"
    work.mkdir(parents=True)
    lease = folder / "Claim.json"
    gate.controller(
        "claim",
        "--pool",
        "grid-fixture",
        "--worker",
        "fixture:grid",
        "--claim-file",
        lease,
    )
    claim = json.loads(lease.read_bytes())
    require(
        claim["job"]["id"] == queue["jobs"][phase], "wrong fixture phase was claimed"
    )
    roles = {**phase_paths(queue, phase), "dispatch": "dispatch.json"}
    files = {}
    for role, relative in roles.items():
        path = work / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = f"disposable {phase} {role}".encode("ascii")
        path.write_bytes(raw)
        files[role] = {"path": relative, "sha256": sha256(raw), "size_bytes": len(raw)}
    result = folder / "Result.json"
    result.write_text(
        canonical(
            {
                "session_version": 0,
                "receipt": {},
                "result": {
                    "outcome": "completed",
                    "records": {},
                    "artifacts": files,
                },
            }
        ),
        encoding="utf-8",
    )
    gate.controller(
        "finish",
        "--lease",
        lease,
        "--result",
        result,
        "--outcome",
        "completed",
        "--reason",
        "disposable transport bytes",
        "--output-root",
        work,
    )


# the same parked id can advance only through the issued dependency selectors
def VerifyGridGate(gate, invoke, scheduled, report, initial):
    assessment, *rescans = scheduled
    job_id = assessment["id"]
    old_pin = initial[job_id]["receipt"]
    queue = QueueFixture(gate, report)
    receipt = gate.write("GridQueue.json", queue)
    queue_pin = sha256(receipt.read_bytes())

    # the process boundary must see an actual issued queue file
    def AttachCall(pin, queue_digest=queue_pin):
        return json.loads(
            invoke(
                "InferenceGrid/Resume.py",
                "--store",
                gate.store,
                "--queue-receipt",
                receipt,
                "--queue-receipt-sha256",
                queue_digest,
                "--parked-receipt-sha256",
                pin,
            )
        )

    # an unrelated pin must not claim the issued queue receipt
    RefuseScope(lambda: AttachCall(old_pin, "1" * 64), "queue receipt pin differs")
    # an unrelated predecessor must not change the parked job
    RefuseScope(lambda: AttachCall("2" * 64), "current parked assessment receipt")
    pending = AttachCall(old_pin)
    require(
        pending["id"] == job_id
        and pending["state"] == "waiting_evidence"
        and pending["attempts"] == 0
        and pending["generation"] > initial[job_id]["generation"],
        "grid attachment did not create a waiting generation of the same assessment",
    )
    require(
        AttachCall(old_pin) == pending,
        "repeating a grid attachment changed its generation",
    )
    gate.controller("artifact", old_pin)
    gate.controller("resource", queue["resource"], "--available")
    FinishFixture(gate, queue, "a")
    incomplete = gate.controller("status", "--job", job_id)["jobs"][0]
    require(
        incomplete["state"] == "waiting_evidence" and incomplete["attempts"] == 0,
        "one completed phase released the grid assessment",
    )
    FinishFixture(gate, queue, "b")
    released = gate.controller("status", "--job", job_id)["jobs"][0]
    require(
        released["state"] == "queued",
        "accepted artifact selectors did not release the next attempt",
    )
    # no cad application is required to prove that forged evidence cannot settle the assessment
    spoof = {**report, "status": "refuted", "counterexamples": {"forged": True}}
    forged = {
        **assessment,
        "id": "fixture:forged-scope-grid",
        "max_attempts": 1,
        "inputs": {
            "plan": gate.bind("fixture:forged-grid", canonical(spoof).encode("utf-8"))
        },
    }
    require(forged["options"]["scope"] == KScopeGap, "wrong parked fixture scope")
    gate.controller("submit", gate.write("ForgedGrid.json", forged))
    statuses = gate.run()
    for failed, message in (
        (
            job_id,
            "scope grid is not a completed authenticated Fusion supervisor attempt",
        ),
        (forged["id"], "the scope hypothesis requires authenticated grid evidence"),
    ):
        require(
            statuses[failed]["state"] == "failed",
            "false scope evidence was not refused",
        )
        artifact = gate.controller("artifact", statuses[failed]["result"])
        payload = json.loads(Path(artifact["path"]).read_bytes())
        require(
            message in (payload.get("stderr_tail") or "")
            and payload.get("result") is None,
            "scope grid failed outside the expected evidence gate",
        )
    require(
        all(
            statuses[job["id"]]["state"] == "waiting_evidence"
            and statuses[job["id"]]["attempts"] == 0
            for job in rescans
        ),
        "forged grid outputs released dependent archive work",
    )
    return {
        "attached_job": job_id,
        "original_receipt": old_pin,
        "native_qualified": False,
    }
