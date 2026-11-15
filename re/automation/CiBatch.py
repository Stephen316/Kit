import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

from Artifacts import Artifacts
from Corpus import git
from Records import canonical, digest, label, specification
from StoreRead import read_store


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def commit_revision(root, revision):
    require(
        re.fullmatch("[0-9a-f]{40}", revision), "batch revision must be a full Git SHA"
    )
    require(
        git(root, "rev-parse", "--verify", revision + "^{commit}").decode().strip()
        == revision,
        "batch revision must identify an existing Git commit",
    )
    return revision


def read_receipt(objects, checksum):
    with objects.path(checksum).open("rb") as source:
        content = source.read(1024 * 1024 + 1)
    require(
        len(content) <= 1024 * 1024 and hashlib.sha256(content).hexdigest() == checksum,
        "waiting attempt receipt failed immutable artifact verification",
    )
    value = json.loads(content)
    require(isinstance(value, dict), "waiting attempt receipt must be an object")
    return value


def waiting_attempt(connection, objects, job):
    receipt = read_receipt(objects, job["receipt"])
    expected = {
        "receipt_version": 1,
        "job_id": job["id"],
        "generation": job["generation"],
        "attempt": job["attempts"],
        "fingerprint": job["fingerprint"],
        "outcome": "waiting_ci",
        "result_sha256": job["result"],
    }
    require(
        all(receipt.get(key) == value for key, value in expected.items())
        and all(
            type(receipt.get(key)) is int
            for key in ("receipt_version", "generation", "attempt")
        )
        and type(receipt.get("execution_id")) is int,
        "receipt does not match the current waiting CI attempt",
    )
    snapshot = json.loads(job["snapshot"])
    require(
        receipt.get("snapshot") == snapshot
        and digest(snapshot) == job["fingerprint"]
        and snapshot["definition_hash"] == job["definition_hash"],
        "waiting CI fingerprint or definition snapshot differs from the receipt",
    )
    attempt = connection.execute(
        "SELECT job_id,generation,number,fingerprint,outcome,receipt,ended "
        "FROM attempts WHERE id=?",
        (receipt["execution_id"],),
    ).fetchone()
    require(
        attempt is not None
        and attempt["ended"] is not None
        and attempt[:6]
        == (
            job["id"],
            job["generation"],
            job["attempts"],
            job["fingerprint"],
            "waiting_ci",
            job["receipt"],
        ),
        "waiting CI receipt does not belong to the settled attempt history",
    )
    return snapshot


def current_member(connection, objects, member, ci_role):
    job = connection.execute(
        "SELECT id,definition,definition_hash,state,generation,fingerprint,snapshot,"
        "attempts,parked,active_attempt,receipt,result FROM jobs WHERE id=?",
        (member,),
    ).fetchone()
    require(
        job is not None
        and job["state"] == "waiting_ci"
        and job["parked"] == 1
        and job["active_attempt"] is None
        and job["attempts"] > 0,
        "each requested job must be parked after a settled waiting CI attempt",
    )
    definition = specification(json.loads(job["definition"]))
    require(
        definition["id"] == member and digest(definition) == job["definition_hash"],
        "waiting CI definition differs from its immutable hash",
    )
    snapshot = waiting_attempt(connection, objects, job)
    binding = definition["inputs"].get(ci_role)
    require(isinstance(binding, str), "waiting CI role must name a controller binding")
    current = connection.execute(
        "SELECT sha256 FROM bindings WHERE name=?", (binding,)
    ).fetchone()
    require(
        current is not None
        and snapshot["inputs"].get(ci_role)
        == {"binding": binding, "sha256": current[0]},
        "waiting CI input differs from its current controller binding",
    )
    for checksum in (
        job["definition_hash"],
        job["fingerprint"],
        job["result"],
        current[0],
    ):
        objects.verify(checksum)
    return {
        "job_id": member,
        "kind": definition["kind"],
        "generation": job["generation"],
        "attempt": job["attempts"],
        "fingerprint": job["fingerprint"],
        "definition_sha256": job["definition_hash"],
        "waiting_receipt_sha256": job["receipt"],
        "waiting_result_sha256": job["result"],
        "ci_binding": binding,
        "ci_input_sha256": current[0],
    }


def frozen_batch(store, revision, members, ci_role):
    require(1 <= len(members) <= 64, "choose 1 to 64 pending CI jobs")
    names = sorted(label(name) for name in members)
    require(len(set(names)) == len(names), "pending CI batch has duplicate job IDs")
    role = label(ci_role)
    objects = Artifacts(store, create=False)
    database = objects.root / "ledger.sqlite3"
    require(
        database.is_file() and not database.is_symlink(),
        "pending CI batch requires an initialized controller store",
    )
    with read_store(database, None, (1, 2, 3, 4)) as connection:
        rows = [current_member(connection, objects, name, role) for name in names]
    payload = {
        "manifest_version": 1,
        "scope": "pending_ci_roster",
        "batch_revision": revision,
        "ci_role": role,
        "members": rows,
    }
    return {**payload, "payload_sha256": digest(payload)}


def main():
    parser = argparse.ArgumentParser(description="Freeze a pending A03 CI batch roster")
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--batch-revision", required=True)
    parser.add_argument("--job", action="append", required=True)
    parser.add_argument("--ci-role", default="ci")
    args = parser.parse_args()
    try:
        revision = commit_revision(
            Path(__file__).resolve().parents[2], args.batch_revision
        )
        print(canonical(frozen_batch(args.store, revision, args.job, args.ci_role)))
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        RecursionError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as error:
        print(f"pending CI batch refused ({type(error).__name__})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
