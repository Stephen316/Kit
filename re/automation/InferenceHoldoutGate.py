# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from pathlib import Path
from struct import pack

from InferenceInputs import sha256
from InferenceRunner import FIELD_KIND
from PairedCaptureIntake import require
from Records import canonical

SCOPE = "synthetic-holdout"
DISCOVERY_LINEAGE = "synthetic-training"
HOLDOUT_LINEAGE = "synthetic-independent"
ENCODING = {"type": "f64", "endian": "little", "unit": "mm", "scale": 1, "offset": 0}


def sample(identity, split, lineage, prefix, expected, stored):
    stream = prefix + pack("<d", stored)
    source = sha256(b"synthetic archive\x00" + identity.encode("ascii") + stream)
    return (
        {
            "id": identity,
            "lineage": lineage,
            "sha256": source,
            "stream": "Synthetic/Parameter",
            "start": len(prefix),
            "length": 8,
            "value": expected,
            "controls": {},
            "role": identity,
            "split": split,
        },
        stream,
        {"archive_sha256": source, "stream_sha256": sha256(stream)},
    )


def submit(gate, case, lineage, stored):
    rows = (
        sample("first", "discovery", DISCOVERY_LINEAGE, b"first", 2.0, 2.0),
        sample("second", "discovery", DISCOVERY_LINEAGE, b"more bytes", 4.0, 4.0),
        sample("withheld", "holdout", lineage, b"separate", 7.0, stored),
    )
    plan = {
        "inference_version": 1,
        "scope": SCOPE,
        "quantity": "length-mm",
        "provenance": {
            "evidence": "synthetic-process-control",
            "inputs": {row["id"]: provenance for row, _, provenance in rows},
        },
        "encodings": [ENCODING],
        "tolerance": 0,
        "confounds": [],
        "observations": [row for row, _, _ in rows],
    }
    inputs = {
        row["role"]: gate.bind(f"{SCOPE}:{case}:{row['id']}", stream)
        for row, stream, _ in rows
    }
    inputs["plan"] = gate.bind(f"{SCOPE}:{case}:plan", canonical(plan).encode("utf-8"))
    job = {
        "id": f"{SCOPE}:{case}",
        "kind": FIELD_KIND,
        "rule_version": "holdout-process@1",
        "tool_version": "inference-archive-gate@1",
        "max_attempts": 1,
        "options": {"scope": SCOPE},
        "inputs": inputs,
    }
    gate.controller("submit", gate.write(f"Holdout-{case}.json", job))
    return job


def verify_holdout(gate):
    accepted = submit(gate, "consistent", HOLDOUT_LINEAGE, 7.0)
    refuted = submit(gate, "contradiction", HOLDOUT_LINEAGE, 9.0)
    repeated = submit(gate, "same-lineage", DISCOVERY_LINEAGE, 7.0)
    statuses = gate.run()
    first = gate.result(accepted, statuses)["assessment"]
    changed = gate.result(refuted, statuses)["assessment"]
    require(
        first["discovery_sha256"] == changed["discovery_sha256"]
        and first["holdout"] != changed["holdout"],
        "withheld evidence changed the frozen discovery identity",
    )
    require(
        len(first["hypotheses"]) == len(changed["hypotheses"]) == 1,
        "synthetic holdout must evaluate one frozen hypothesis",
    )
    consistent = first["hypotheses"][0]
    contradicted = changed["hypotheses"][0]
    require(
        consistent["id"] == contradicted["id"]
        and consistent["discovery"] == contradicted["discovery"]
        and consistent["confidence"] == "partial"
        and consistent["holdout"][0]["status"] == "pattern"
        and not first["counterexamples"]
        and contradicted["confidence"] == "refuted"
        and contradicted["holdout"][0]["status"] == "mismatch"
        and changed["counterexamples"]
        == [{"hypothesis": consistent["id"], "split": "holdout", "sample": "withheld"}],
        "withheld evidence did not independently confirm or refute the same hypothesis",
    )
    refusal = statuses[repeated["id"]]
    require(
        refusal["state"] == "failed" and refusal["attempts"] == 1 and refusal["result"],
        "same-lineage holdout was not refused by the supervised runner",
    )
    failure_path = gate.controller("artifact", refusal["result"])["path"]
    payload = json.loads(Path(failure_path).read_bytes())
    stderr = payload.get("stderr_tail") or ""
    require(
        "lineage" in stderr and "holdout" in stderr and payload.get("result") is None,
        "same-lineage holdout failed for an unexpected reason",
    )
    return {
        "evidence": "synthetic-process-control",
        "discovery_sha256": first["discovery_sha256"],
        "hypothesis": consistent["id"],
        "accepted_holdout": consistent["holdout"],
        "contradicted_holdout": contradicted["holdout"],
        "same_lineage_refusal": refusal["receipt"],
    }
