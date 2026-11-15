"""Rebind exact paired-discovery attempts using live authenticated hosted evidence."""

import argparse
import os
import sqlite3
import subprocess
from pathlib import Path

from Artifacts import Artifacts
from CiBatch import current_member, read_receipt, require
from CiBatchTerminal import GitHubRead, checked_roster, member_name, sha
from Ledger import Ledger, pending_ci_inputs
from Records import canonical, digest, read_record

KIND = "candidate.paired-discovery"
SCOPE = "p01-p03-p04-paired-reader-discovery"


def pending_input(revision):
    return {"schema": 1, "status": "pending", "candidate_revision": revision, "scope": SCOPE}


def stage_record(objects, member, revision):
    require(member["kind"] == KIND, "release supports only paired discovery members")
    previous = read_receipt(objects, member["ci_input_sha256"])
    require(
        canonical(previous) == canonical(pending_input(revision)),
        "parked candidate CI input differs from this batch revision",
    )
    stage = read_receipt(objects, member["waiting_result_sha256"])["result"]
    record = stage["records"]
    require(
        stage["outcome"] == "waiting_ci"
        and type(record["schema"]) is int
        and record["schema"] == 1
        and record["scope"] == SCOPE
        and record["candidate_revision"] == revision
        and record["native_qualified"] is False
        and record["fresh_native_fusion"] == "unverified"
        and record["counterexamples"] == []
        and set(record["evidence_sha256"]) == {"rectangles", "principal", "cut"}
        and all(sha(value, 64) for value in record["evidence_sha256"].values()),
        "parked result does not contain successful paired discovery research",
    )
    return record


def expected_saves(objects, roster):
    require(roster["ci_role"] == "ci", "paired discovery must use the ci input role")
    saves = {
        digest(stage_record(objects, member, roster["batch_revision"])["saves"])
        for member in roster["members"]
    }
    require(len(saves) == 1, "paired discovery batch members must have the same save roster")
    return saves.pop()


def verified_pass(roster, observed, saves):
    require(observed["status"] == "archive_gate_verified", "hosted archive gate is not verified")
    aggregate = observed["aggregate"]
    gate = observed["archive_gate"]
    receipt = gate["receipt"]
    origin = receipt["origin"]
    require(
        aggregate["status"] == "aggregate_success_attested"
        and aggregate["roster_payload_sha256"] == roster["payload_sha256"]
        and aggregate["batch_revision"] == roster["batch_revision"] == origin["head_sha"]
        and aggregate["repository"] == origin["repository"]
        and aggregate["pull_number"] == origin["pull_request"]
        and aggregate["base_sha"] == origin["base_sha"]
        and aggregate["head_tree_sha"] == origin["head_tree"]
        and aggregate["tested_merge_sha"] == origin["tested_sha"]
        and aggregate["tested_tree_sha"] == origin["tested_tree"]
        and origin["head_tree"] == origin["tested_tree"]
        and receipt["scope"] == "hosted_paired_archive_gate"
        and gate["receipt_sha256"] == digest(receipt)
        and receipt["corpus"]["saves_sha256"] == saves == digest(receipt["corpus"]["saves"]),
        "aggregate, archive gate and parked candidate evidence differ",
    )
    return {
        "repository": aggregate["repository"],
        "pull_number": aggregate["pull_number"],
        "base_sha": aggregate["base_sha"],
        "tested_commit": aggregate["tested_merge_sha"],
        "tested_tree": aggregate["tested_tree_sha"],
        "aggregate_run": aggregate["run_id"],
        "aggregate_attempt": aggregate["run_attempt"],
        "aggregate_artifact": aggregate["evidence_artifact_id"],
        "aggregate_artifact_digest": aggregate["evidence_artifact_digest"],
        "archive_run": origin["run_id"],
        "archive_attempt": origin["run_attempt"],
        "archive_artifact": gate["artifact_id"],
        "archive_artifact_digest": gate["artifact_digest"],
        "archive_receipt_sha256": gate["receipt_sha256"],
    }


def member_input(roster, member, stage, proof, observation_sha256):
    return {
        **pending_input(roster["batch_revision"]),
        "status": "passed",
        "roster_sha256": roster["payload_sha256"],
        "member": member,
        "stage_record_sha256": digest(stage),
        "saves_sha256": digest(stage["saves"]),
        "verification": proof,
        "observation_sha256": observation_sha256,
    }


def changed_snapshot(original, member, new_digest):
    updated = dict(original)
    updated["inputs"] = {
        **original["inputs"],
        "ci": {"binding": member["ci_binding"], "sha256": new_digest},
    }
    return updated


def release(ledger, roster, observed):
    revision = roster["batch_revision"]
    saves = expected_saves(ledger.objects, roster)
    proof = verified_pass(roster, observed, saves)
    observation_sha256 = digest({"roster": roster, "observation": observed})
    entries = []
    for member in roster["members"]:
        name, binding = member["job_id"], member["ci_binding"]
        owners = ledger.db.execute(
            "SELECT job_id FROM job_inputs WHERE binding=?", (binding,)
        ).fetchall()
        definition = read_receipt(ledger.objects, member["definition_sha256"])
        prior = read_receipt(ledger.objects, member["fingerprint"])
        require(
            [row[0] for row in owners] == [name]
            and list(role for role, target in definition["inputs"].items() if target == binding) == ["ci"]
            and definition["options"] == {"candidate_revision": revision}
            and not pending_ci_inputs(prior),
            "member must have one dedicated CI input and no provisional prerequisite",
        )
        stage = stage_record(ledger.objects, member, revision)
        record = member_input(roster, member, stage, proof, observation_sha256)
        checksum = digest(record)
        fingerprint = digest(changed_snapshot(prior, member, checksum))
        current = ledger.db.execute(
            "SELECT generation,fingerprint FROM jobs WHERE id=?", (name,)
        ).fetchone()
        applied = current is not None and tuple(current) == (member["generation"] + 1, fingerprint)
        if applied:
            linked = ledger.db.execute("SELECT sha256 FROM bindings WHERE name=?", (binding,)).fetchone()
            require(linked is not None and linked[0] == checksum, "existing release binding differs")
            ledger.verify_object(checksum)
        else:
            require(
                current_member(ledger.db, ledger.objects, name, "ci") == member,
                "parked member changed after the roster was frozen",
            )
        entries.append((member, record, checksum, fingerprint, applied))
    if all(entry[-1] for entry in entries):
        ledger.verify_object(observation_sha256)
        return {"status": "already_released", "observation_sha256": observation_sha256}
    require(not any(entry[-1] for entry in entries), "only part of the batch has this exact release")
    require(
        ledger.objects.put_record({"roster": roster, "observation": observed}) == observation_sha256,
        "CI batch observation digest changed before publication",
    )
    for member, record, checksum, _, _ in entries:
        require(ledger.objects.put_record(record) == checksum, "member release digest changed")
        ledger.set_binding(member["ci_binding"], checksum)
    ledger.refresh()
    for member, _, _, fingerprint, _ in entries:
        job = ledger.db.execute(
            "SELECT generation,fingerprint,state FROM jobs WHERE id=?", (member["job_id"],)
        ).fetchone()
        require(
            tuple(job) == (member["generation"] + 1, fingerprint, "queued"),
            "CI binding did not queue the exact successor generation",
        )
    ledger.event(None, "ci_batch_released", {
        "observation_sha256": observation_sha256,
        "roster_sha256": roster["payload_sha256"],
        "members": [entry[0]["job_id"] for entry in entries],
    })
    return {"status": "released", "observation_sha256": observation_sha256}


def resumed_member(packet, record):
    job = packet["job"]
    revision = job["options"]["candidate_revision"]
    member = record["member"]
    member_name(member)
    inputs = {
        role: {"binding": item["binding"], "sha256": item["sha256"]}
        for role, item in packet["inputs"].items()
    }
    require(
        set(record) == set(pending_input(revision)) | {
            "roster_sha256", "member", "stage_record_sha256", "saves_sha256",
            "verification", "observation_sha256",
        }
        and type(record["schema"]) is int
        and record["schema"] == 1
        and record["status"] == "passed"
        and record["scope"] == SCOPE
        and record["candidate_revision"] == revision
        and member["job_id"] == job["id"]
        and member["kind"] == job["kind"] == KIND
        and member["definition_sha256"] == digest(job)
        and packet["generation"] == member["generation"] + 1
        and inputs["ci"]["binding"] == member["ci_binding"]
        and isinstance(record["verification"], dict)
        and all(sha(record[key], 64) for key in (
            "roster_sha256", "stage_record_sha256", "saves_sha256", "observation_sha256"
        )),
        "CI input does not name the exact paired discovery successor",
    )
    snapshot = {
        "definition_hash": member["definition_sha256"],
        "dependencies": packet["dependencies"],
        "inputs": inputs,
    }
    require(
        digest(snapshot) == packet["fingerprint"]
        and digest(changed_snapshot(snapshot, member, member["ci_input_sha256"])) == member["fingerprint"],
        "CI release changed inputs beyond the CI result binding",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--roster-sha256", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pull", type=int, required=True)
    parser.add_argument("--aggregate-run", type=int, required=True)
    parser.add_argument("--aggregate-attempt", type=int, required=True)
    parser.add_argument("--workflow-run", type=int, required=True)
    parser.add_argument("--workflow-attempt", type=int, required=True)
    parser.add_argument("--audited-revision", required=True)
    args = parser.parse_args()
    try:
        from CiArchiveObservation import observe

        roster = checked_roster(read_record(args.roster), args.roster_sha256)
        args.saves_sha256 = expected_saves(Artifacts(args.store, create=False), roster)
        api = GitHubRead(args.repository, os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
        evidence = observe(
            api, args, validated_roster=(roster["batch_revision"], roster["payload_sha256"])
        )
        aggregate_status = (evidence.get("aggregate") or {}).get("status")
        if evidence["status"] != "archive_gate_verified" or aggregate_status != "aggregate_success_attested":
            print(canonical({
                "status": "waiting_ci",
                "observation": evidence["status"],
                "aggregate": aggregate_status,
            }))
            return 0
        with Ledger(args.store) as ledger:
            response = release(ledger, roster, evidence)
        print(canonical(response))
        return 0
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error, subprocess.SubprocessError) as error:
        parser.exit(1, f"CI batch release refused: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
