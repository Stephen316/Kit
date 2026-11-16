# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Corpus import git
from InferenceArchives import REVISION, ROOT, archive_gaps
from InferenceGrid.Evidence import KScopeGap, KScopeSpecPin
from InferenceGrid.Resume import BindGrid
from InferenceRunner import FORMATS, GAP_KIND
from InferenceSchedule import build_schedule
from Ledger import Ledger
from PairedCaptureIntake import require, sha256
from PriorityPlan import schedule_plan
from PrioritySchedule import schedule
from Records import canonical, digest

# the portable store must assess the same frozen discovery hypothesis
KScopeReportPin = "557028a830ea0fa5e55bb0ebf797e657f8be3b4e06046937bb1b7cb787c48818"


# the job records its actual source so another checkout cannot claim its evidence
def CheckRevision(revision):
    require(
        re.fullmatch(r"[0-9a-f]{40}", revision)
        and git(ROOT, "rev-parse", "HEAD").decode("ascii").strip() == revision,
        "scope provisioning requires the exact checked out source revision",
    )
    require(
        not git(
            ROOT,
            "status",
            "--porcelain=v1",
            "--",
            "re/automation",
            "re/Fusion/Study",
            "src",
        ),
        "scope provisioning requires clean research and reader sources",
    )


# only the parked scope and its original consequent rescans belong in this store
def ScopeSchedule(revision):
    gaps, native = archive_gaps()
    (report,) = (gap for gap in gaps if gap["scope"] == KScopeGap)
    archives = report["affected_archives"]
    require(
        report["capture_revision"] == REVISION
        and report["requested_grid"]["sha256"] == KScopeSpecPin
        and digest(report) == KScopeReportPin
        and len(archives) == 2
        and set(archives.values()) == FORMATS,
        "P04 scope report differs from the pinned discovery plan",
    )
    plan_binding = "inference-scope:" + KScopeReportPin
    archive_inputs = {
        pin: {"binding": "inference-scope-archive:" + pin, "format": source_format}
        for pin, source_format in sorted(archives.items())
    }
    sources = {}
    for pin, item in archive_inputs.items():
        recorded_format, data = native[pin]
        require(
            recorded_format == item["format"] and sha256(data) == pin,
            "P04 scope source differs from the pinned archive",
        )
        sources[item["binding"]] = (pin, data)
    batch = build_schedule(
        {
            "inference_version": 1,
            "scope": KScopeGap,
            "family": report["recipe_family"],
            "rule_version": "archive-field-search@1",
            "tool_version": revision,
            "plan_input": plan_binding,
            "stream_inputs": {},
            "archives": archive_inputs,
            "distinguishing_evidence": [],
            "depends_on": [],
            "assessment_kind": GAP_KIND,
        }
    )
    return report, plan_binding, sources, batch


# a repeat provision must never replace existing scope jobs or their priority
def HasScopePlan(ledger, batch):
    jobs, priorities = schedule_plan(batch)
    present = 0
    for job_id, spec in jobs.items():
        row = ledger.db.execute(
            "SELECT definition_hash FROM jobs WHERE id=?", (job_id,)
        ).fetchone()
        if row is None:
            continue
        present += 1
        priority = ledger.db.execute(
            "SELECT lane,family,documents,evidence,installation,definition_hash "
            "FROM a07_priority WHERE job_id=?",
            (job_id,),
        ).fetchone()
        lane, family, documents, evidence, installation = priorities[job_id]
        require(
            row[0] == digest(spec)
            and priority is not None
            and tuple(priority)
            == (
                lane,
                family,
                canonical(documents),
                canonical(evidence),
                installation,
                row[0],
            ),
            "existing P04 scope job or priority has a different definition",
        )
    require(present in (0, len(jobs)), "only part of the P04 scope schedule exists")
    return bool(present)


# offline scheduling creates ordinary controller dependencies for the local worker
def ProvisionScope(store, revision):
    CheckRevision(revision)
    report, plan_binding, sources, batch = ScopeSchedule(revision)
    with (
        Ledger(store) as ledger,
        TemporaryDirectory(prefix="kit-scope-provision-") as scratch,
    ):
        exists = HasScopePlan(ledger, batch)
        BindGrid(ledger, plan_binding, KScopeReportPin)
        for binding, (pin, _) in sources.items():
            BindGrid(ledger, binding, pin)
        require(
            ledger.objects.put_record(report) == KScopeReportPin,
            "stored P04 scope report differs from the verified plan",
        )
        for pin, data in sources.values():
            staged = Path(scratch) / pin
            staged.write_bytes(data)
            require(
                ledger.objects.put_file(staged) == pin,
                "stored P04 scope archive digest differs",
            )
        if not exists:
            schedule(ledger, batch)
        return {
            "scope": KScopeGap,
            "source_revision": revision,
            "capture_revision": REVISION,
            "plan_sha256": KScopeReportPin,
            "assessment_job": batch["jobs"][0]["id"],
            "jobs": [ledger.status(job["id"])["jobs"][0] for job in batch["jobs"]],
        }


# the host owner can schedule the exact assessment without importing another store
def MainProvision():
    parser = argparse.ArgumentParser(
        description="Provision the pinned P04 discovery scope in a local A03 store"
    )
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    try:
        print(canonical(ProvisionScope(args.store, args.source_revision)))
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as error:
        parser.exit(1, f"P04 scope provision refused: {error}\n")


if __name__ == "__main__":
    MainProvision()
