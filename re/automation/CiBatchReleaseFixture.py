"""Exercise paired batch rebinding through a disposable A03 store in hosted CI."""

import argparse
from pathlib import Path

from CiBatch import commit_revision, frozen_batch
from CiBatchRelease import KIND, SCOPE, pending_input, release, resumed_member
from Corpus import git
from Ledger import Ledger
from Records import canonical, digest, read_record


def queue(root, revision, saves):
    root.mkdir()
    store = root / "store"
    pending = root / "pending.json"
    pending.write_text(canonical(pending_input(revision)), encoding="utf-8")
    ids = ("candidate:first", "candidate:next")
    with Ledger(store, True) as ledger:
        for name in ids:
            binding = f"ci:{name}"
            ledger.bind(binding, pending)
            ledger.submit({
                "id": name,
                "kind": KIND,
                "options": {"candidate_revision": revision},
                "inputs": {"ci": binding},
                "rule_version": "paired@1",
                "tool_version": revision,
            })
        for expected in ids:
            lease = ledger.claim("fixture:discovery")
            assert lease["job"]["id"] == expected
            records = {
                "schema": 1, "scope": SCOPE, "candidate_revision": revision,
                "native_qualified": False, "fresh_native_fusion": "unverified",
                "evidence_sha256": {name: digest(name) for name in ("rectangles", "principal", "cut")},
                "saves": saves, "counterexamples": [],
            }
            ledger.finish(
                expected, lease["lease_token"], "waiting_ci", pending,
                "fixture discovery parked",
                result_record={"result": {"outcome": "waiting_ci", "records": records}},
            )
    return store, frozen_batch(store, revision, ids, "ci")


def observation(roster, saves):
    head = roster["batch_revision"]
    origin = {
        "repository": "fixture/kit", "pull_request": 94,
        "base_sha": "b" * 40, "head_sha": head, "head_tree": "1" * 40,
        "tested_sha": "a" * 40, "tested_tree": "1" * 40, "run_id": 12, "run_attempt": 1,
    }
    receipt = {
        "scope": "hosted_paired_archive_gate", "origin": origin,
        "corpus": {"saves_sha256": digest(saves), "saves": saves},
    }
    return {
        "status": "archive_gate_verified",
        "aggregate": {
            "status": "aggregate_success_attested", "roster_payload_sha256": roster["payload_sha256"],
            "repository": origin["repository"], "pull_number": 94,
            "batch_revision": head, "base_sha": origin["base_sha"], "head_tree_sha": origin["head_tree"],
            "tested_merge_sha": origin["tested_sha"], "tested_tree_sha": origin["tested_tree"],
            "run_id": 11, "run_attempt": 1, "evidence_artifact_id": 13,
            "evidence_artifact_digest": "sha256:" + "3" * 64,
        },
        "archive_gate": {
            "receipt": receipt, "receipt_sha256": digest(receipt), "artifact_id": 14,
            "artifact_digest": "sha256:" + "4" * 64,
        },
    }


def exact_resume(ledger, roster):
    acquired = ledger.claim("fixture:resumed")
    snapshot = acquired["snapshot"]
    content = ledger.objects.path(snapshot["inputs"]["ci"]["sha256"])
    member = read_record(content)
    packet = {
        **{name: acquired[name] for name in ("job", "generation", "fingerprint")},
        "dependencies": snapshot["dependencies"], "inputs": snapshot["inputs"],
    }
    assert member["roster_sha256"] == roster["payload_sha256"]
    resumed_member(packet, member)
    member["member"] = roster["members"][1]
    try:
        resumed_member(packet, member)
    except ValueError:
        return
    raise AssertionError("resumed job accepted another member's evidence")


def exercise(root, revision):
    saves = {"P01": {"baseline-a": {"fusion": "1" * 64, "solidworks": "2" * 64}}}
    store, roster = queue(root / "ready", revision, saves)
    with Ledger(store) as ledger:
        report = observation(roster, saves)
        assert release(ledger, roster, report)["status"] == "released"
        assert release(ledger, roster, report)["status"] == "already_released"
        assert [row["state"] for row in ledger.status()["jobs"]] == ["queued", "queued"]
        exact_resume(ledger, roster)
    store, roster = queue(root / "stale", revision, saves)
    other = root / "updated.json"
    other.write_text('{"new":"input"}', encoding="utf-8")
    with Ledger(store) as ledger:
        ledger.bind("ci:candidate:next", other)
    database = store / "ledger.sqlite3"
    original = database.read_bytes()
    try:
        with Ledger(store) as ledger:
            release(ledger, roster, observation(roster, saves))
    except ValueError as error:
        assert "parked after a settled" in str(error)
    else:
        raise AssertionError("a stale member was released")
    assert database.read_bytes() == original
    return {"released_members": 2, "exact_resume": True, "stale_batch_untouched": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    revision = commit_revision(root, git(root, "rev-parse", "HEAD").decode().strip())
    print(canonical(exercise(args.directory, revision)))
