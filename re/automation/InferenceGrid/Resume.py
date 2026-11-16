# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from InferenceGrid.Evidence import CheckGridPlan, GridInputs, KScopeGap
from InferenceInputs import checksum, sha256
from InferenceRunner import GAP_KIND
from Ledger import Ledger
from PairedCaptureIntake import require
from PrioritySchedule import schedule
from Records import canonical, digest, read_record, specification

from ApplicationProtocol import file_bytes
from AuditFusionPhases import StoreSnapshot, phase_row, verify_binding


# a successor must replace the exact still parked assessment and retain its attempt record
def ParkedGrid(ledger, job, pin):
    require(
        job is not None
        and job["state"] == "waiting_evidence"
        and job["parked"] == 1
        and job["receipt"] == pin,
        "expected the current parked assessment receipt",
    )
    ledger.verify_object(pin)
    receipt = read_record(ledger.objects.path(pin))
    spec = specification(json.loads(job["definition"]))
    snapshot = json.loads(job["snapshot"])
    require(
        receipt["receipt_version"] == 1
        and receipt["job_id"] == spec["id"] == job["id"]
        and receipt["outcome"] == "waiting_evidence"
        and receipt["result_sha256"] == job["result"]
        and receipt["generation"] == job["generation"]
        and receipt["attempt"] == job["attempts"]
        and receipt["fingerprint"] == job["fingerprint"] == digest(snapshot)
        and receipt["snapshot"] == snapshot
        and snapshot["definition_hash"] == job["definition_hash"] == digest(spec)
        and spec["kind"] == GAP_KIND
        and spec["options"] == {"scope": KScopeGap}
        and set(spec["inputs"]) == {"plan"}
        and isinstance(spec["inputs"]["plan"], str),
        "parked receipt does not identify the original scope assessment",
    )
    ledger.verify_result(job["result"])
    outcome = read_record(ledger.objects.path(job["result"]))["result"]
    plan_pin = snapshot["inputs"]["plan"]["sha256"]
    ledger.verify_object(plan_pin)
    report = read_record(ledger.objects.path(plan_pin))
    require(
        outcome["outcome"] == "waiting_evidence"
        and outcome["records"]["report_sha256"] == plan_pin
        and outcome["records"]["assessment"] == report,
        "parked scope request differs from its accepted runner report",
    )
    return spec, report


# extending one scheduled assessment must preserve its existing priority and downstream job id
def GridSchedule(ledger, spec, choices):
    priority = ledger.db.execute(
        "SELECT lane,family,documents,evidence,installation,definition_hash "
        "FROM a07_priority WHERE job_id=?",
        (spec["id"],),
    ).fetchone()
    require(
        priority is not None
        and priority["lane"] == 1
        and priority["installation"] is None
        and priority["definition_hash"] == digest(spec),
        "parked assessment does not have its original inference priority",
    )
    schedule(
        ledger,
        {
            "schedule_version": 1,
            "jobs": [choices],
            "priority": [
                {
                    "id": spec["id"],
                    "family": priority["family"],
                    "documents": json.loads(priority["documents"]),
                    "distinguishing_evidence": json.loads(priority["evidence"]),
                }
            ],
        },
    )


# content addressed resume bindings must stay immutable across repeated attachments
def BindGrid(ledger, name, pin):
    old = ledger.db.execute(
        "SELECT sha256 FROM bindings WHERE name=?", (name,)
    ).fetchone()
    require(old is None or old[0] == pin, "scope grid content binding has changed")
    if old is None:
        ledger.set_binding(name, pin)


# the controller wakes the same assessment only when the queued native artifacts exist
def AttachGrid(store, queue, pin):
    checksum(pin)
    selectors = GridInputs(queue, pin)
    job_id = "inference:" + digest(KScopeGap)
    with (
        Ledger(store) as ledger,
        TemporaryDirectory(prefix="kit-grid-attach-") as scratch,
    ):
        current = ledger.status(job_id)["jobs"]
        require(len(current) == 1, "the fixed A07 scope assessment is not scheduled")
        job = ledger.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        existing = specification(json.loads(job["definition"]))
        previous = {
            role: value for role, value in existing["inputs"].items() if role != "plan"
        }
        if previous:
            require(
                previous == selectors
                and existing["options"]
                == {"scope": KScopeGap, "grid_from_receipt": pin},
                "a different grid or parked attempt is already attached",
            )
            return current[0]
        spec, report = ParkedGrid(ledger, job, pin)
        owner = StoreSnapshot(ledger.db, store)
        plan = verify_binding(owner, queue, Path(scratch))
        CheckGridPlan(report, plan)
        first, second = [phase_row(owner, queue, phase) for phase in ("a", "b")]
        require(
            first["kind"] == second["kind"], "queued Fusion grid phase kinds differ"
        )
        queue_pin = ledger.objects.put_record(queue)
        BindGrid(ledger, selectors["grid-queue"], queue_pin)
        BindGrid(ledger, selectors["grid-previous"], pin)
        successor = {
            **spec,
            "depends_on": sorted(set(spec["depends_on"]) | set(queue["jobs"].values())),
            "inputs": {**spec["inputs"], **selectors},
            "options": {**spec["options"], "grid_from_receipt": pin},
        }
        GridSchedule(ledger, spec, successor)
        return ledger.status(job_id)["jobs"][0]


# explicit pin arguments keep manual report files outside the admission boundary
def MainGrid():
    parser = argparse.ArgumentParser(
        description="Attach the exact queued Fusion scope grid to its parked A07 assessment"
    )
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--queue-receipt", type=Path, required=True)
    parser.add_argument("--queue-receipt-sha256", required=True)
    parser.add_argument("--parked-receipt-sha256", required=True)
    args = parser.parse_args()
    try:
        raw = file_bytes(args.queue_receipt, 1024 * 1024)
        require(
            sha256(raw) == checksum(args.queue_receipt_sha256),
            "scope grid queue receipt pin differs",
        )
        print(
            canonical(
                AttachGrid(args.store, json.loads(raw), args.parked_receipt_sha256)
            )
        )
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error) as error:
        parser.exit(1, f"inference grid attachment refused: {error}\n")


if __name__ == "__main__":
    MainGrid()
