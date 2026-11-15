"""Observe an audited hosted archive gate without settling batch members."""

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path

from CiBatchTerminal import (
    HOST,
    GitHubRead,
    artifact_receipt,
    latest_run,
    load_roster,
    observe as observe_aggregate,
    pull_identity,
    require,
    run_identity,
    sha,
)
from CiPairedArchiveGate import APPLICATIONS, CHECKS, COUNTS, GATE_STEP, ROOT, WORKFLOW
from Corpus import git
from Records import canonical, digest

EVENT = "pull_request"
JOB_NAME = "Verify CI policy and pytest compatibility"
WORKFLOW_NAME = "Workflow quality"
PRODUCER = "re/automation/CiPairedArchiveGate.py"
GATE_STEPS = (
    GATE_STEP,
    "Bind the paired archive gate receipt",
    "Publish paired archive gate receipt",
)
ACTIONS_APP = 15368


def positive(value):
    return type(value) is int and value > 0


def workflow_run(api, run_id, pull):
    value = api.record(f"actions/runs/{run_id}")
    require(
        value["id"] == run_id
        and value["event"] == EVENT
        and value["path"].split("@", 1)[0] == WORKFLOW
        and value["repository"]["id"] == pull["repository_id"]
        and value["head_repository"]["id"] == pull["head_repository_id"]
        and value["head_sha"] == pull["head_sha"]
        and positive(value["workflow_id"])
        and positive(value["check_suite_id"])
        and (
            not value["pull_requests"]
            or any(
                row["number"] == pull["pull_number"] for row in value["pull_requests"]
            )
        ),
        "archive run does not match the current pull request and workflow",
    )
    return {
        key: value[key]
        for key in (
            "workflow_id",
            "check_suite_id",
            "run_attempt",
            "status",
            "conclusion",
        )
    }


def policy_job(api, run_id, attempt, run, pull):
    listing = api.record(f"actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100")
    require(
        listing["total_count"] == len(listing["jobs"]),
        "archive workflow job listing is incomplete",
    )
    jobs = [job for job in listing["jobs"] if job["name"] == JOB_NAME]
    require(len(jobs) == 1, "expected a unique hosted archive policy job")
    job = jobs[0]
    require(
        positive(job["id"])
        and job["run_id"] == run_id
        and job["run_attempt"] == attempt
        and job["head_sha"] == pull["head_sha"]
        and job["workflow_name"] == WORKFLOW_NAME
        and job["status"] == "completed"
        and job["conclusion"] == "success"
        and job["check_run_url"]
        == f"https://{HOST}/repos/{pull['repository']}/check-runs/{job['id']}",
        "archive policy job lacks an exact successful run attempt",
    )
    check = api.record(f"check-runs/{job['id']}")
    require(
        all(
            check[key] == job[key]
            for key in ("id", "name", "head_sha", "status", "conclusion")
        )
        and check["app"]["id"] == ACTIONS_APP
        and check["check_suite"]["id"] == run["check_suite_id"]
        and check["details_url"] == job["html_url"],
        "archive job does not match the authenticated Actions check run",
    )
    observed = []
    for name in GATE_STEPS:
        steps = [step for step in job["steps"] if step["name"] == name]
        require(len(steps) == 1, "expected one step for each archive gate operation")
        step = steps[0]
        require(
            positive(step["number"])
            and step["status"] == "completed"
            and step["conclusion"] == "success",
            "archive gate step lacks observed success",
        )
        observed.append(step["number"])
    require(observed == sorted(set(observed)), "archive gate step order differs")
    return job["id"]


def audited_checkout(api, pull, audited_revision):
    head_sha, merge_sha = (pull[key] for key in ("head_sha", "merge_sha"))
    require(
        all(
            sha(value, 40)
            for value in (head_sha, merge_sha, pull["base_sha"], audited_revision)
        ),
        "archive observation needs a valid exact merge and audited revision",
    )
    head = api.record(f"git/commits/{head_sha}")
    merge = api.record(f"git/commits/{merge_sha}")
    head_tree, merge_tree = (row["tree"]["sha"] for row in (head, merge))
    local = git(ROOT, "rev-parse", "--verify", f"{audited_revision}^{{commit}}")
    require(
        local.decode("ascii").strip() == audited_revision
        and head["sha"] == head_sha
        and merge["sha"] == merge_sha
        and [parent["sha"] for parent in merge["parents"]]
        == [pull["base_sha"], head_sha]
        and sha(head_tree, 40)
        and sha(merge_tree, 40)
        and git(ROOT, "rev-parse", f"{audited_revision}^{{tree}}")
        .decode("ascii")
        .strip()
        == merge_tree,
        "authenticated archive merge tree differs from the explicitly audited revision",
    )
    return {"head_tree": head_tree, "tested_sha": merge_sha, "tested_tree": merge_tree}


def source_blob(api, path, tested, audited):
    local = git(ROOT, "rev-parse", f"{audited}:{path}").decode("ascii").strip()
    remote = api.record(f"contents/{path}?ref={tested}")
    require(
        sha(local, 40)
        and remote["path"] == path
        and remote["type"] == "file"
        and remote["sha"] == local,
        "hosted archive gate source differs from the audited Git blob",
    )
    return local


def verify_receipt(api, receipt, origin, audited, saves_sha256):
    require(
        type(receipt["schema"]) is int
        and receipt["schema"] == 1
        and receipt["scope"] == "hosted_paired_archive_gate"
        and set(receipt) == {"schema", "scope", "origin", "checks", "corpus"},
        "invalid hosted archive gate receipt",
    )
    observed = receipt["origin"]
    require(
        type(observed) is dict
        and set(observed)
        == set(origin) | {"workflow_sha", "workflow_ref", "workflow_blob"}
        and all(observed.get(key) == value for key, value in origin.items())
        and sha(observed["workflow_sha"], 40)
        and isinstance(observed["workflow_ref"], str)
        and observed["workflow_ref"].startswith(f"{origin['repository']}/{WORKFLOW}@"),
        "hosted archive receipt lineage differs from the authenticated job",
    )
    tested = origin["tested_sha"]
    workflow_blob = source_blob(api, WORKFLOW, tested, audited)
    workflow_ref = api.record(f"contents/{WORKFLOW}?ref={observed['workflow_sha']}")
    require(
        workflow_blob == observed["workflow_blob"] == workflow_ref["sha"]
        and workflow_ref["path"] == WORKFLOW
        and workflow_ref["type"] == "file",
        "reported workflow source differs from its independent audited pin",
    )
    collector = source_blob(api, PRODUCER, tested, audited)
    expected_checks = [
        {
            "nodeid": node,
            "outcome": "passed",
            "test_blob": source_blob(api, node.split("::", 1)[0], tested, audited),
        }
        for node in CHECKS
    ]
    require(
        receipt["checks"] == expected_checks, "archive receipt check roster differs"
    )
    corpus = receipt["corpus"]
    saves, receipts = (corpus[key] for key in ("saves", "receipts"))
    require(
        type(corpus) is dict
        and set(corpus)
        == {
            "capture_revision",
            "specification_sha256",
            "receipts",
            "counts",
            "saves",
            "saves_sha256",
        }
        and sha(corpus["capture_revision"], 40)
        and sha(corpus["specification_sha256"], 64)
        and corpus["counts"] == COUNTS
        and set(saves) == set(receipts) == set(COUNTS)
        and digest(saves) == corpus["saves_sha256"] == saves_sha256,
        "hosted archive receipt does not match the fixed discovery roster",
    )
    for family, count in COUNTS.items():
        roster = saves[family]
        require(
            len(roster) == count
            and set(receipts[family]) == set(APPLICATIONS)
            and all(sha(pin, 64) for pin in receipts[family].values())
            and all(
                set(pair) == set(APPLICATIONS)
                and all(sha(pin, 64) for pin in pair.values())
                for pair in roster.values()
            )
            and all(
                roster["baseline-a"][app] != roster["baseline-b"][app]
                for app in APPLICATIONS
            ),
            "hosted archive receipt lacks the expected application save pins",
        )
    return collector


def observe(api, args, *, validated_roster=None):
    if validated_roster is None:
        validated_roster = load_roster(args.roster, args.roster_sha256)
    revision, roster_hash = validated_roster
    require(
        sha(revision, 40)
        and sha(roster_hash, 64)
        and roster_hash == args.roster_sha256,
        "archive observation roster provenance differs",
    )
    initial_pull = pull_identity(api, args.pull)
    aggregate = observe_aggregate(
        api,
        args.repository,
        revision,
        roster_hash,
        args.pull,
        args.aggregate_run,
        args.aggregate_attempt,
    )
    result = {
        "report_version": 1,
        "scope": "paired_archive_gate_observation",
        "aggregate": aggregate,
        "audited_revision": args.audited_revision,
        "member_attribution": "unavailable",
    }
    if aggregate["status"] in ("superseded", "pending"):
        return {**result, "status": aggregate["status"]}
    require(
        aggregate["status"]
        in ("aggregate_success_attested", "aggregate_failure_unattributed"),
        "archive gate requires an observed terminal aggregate",
    )
    pull = pull_identity(api, args.pull)
    if pull != initial_pull or pull["state"] != "open" or pull["head_sha"] != revision:
        return {**result, "status": "superseded"}
    run = workflow_run(api, args.workflow_run, pull)
    if run["run_attempt"] != args.workflow_attempt or not latest_run(
        api, pull, run["workflow_id"], args.workflow_run, EVENT
    ):
        return {**result, "status": "superseded"}
    if run["status"] != "completed":
        return {**result, "status": "pending"}
    workflow = api.record(f"actions/workflows/{run['workflow_id']}")
    require(
        workflow["id"] == run["workflow_id"] and workflow["path"] == WORKFLOW,
        "archive workflow ID does not match its trusted path",
    )
    job = policy_job(api, args.workflow_run, args.workflow_attempt, run, pull)
    checkout = audited_checkout(api, pull, args.audited_revision)
    if aggregate["status"] == "aggregate_success_attested":
        require(
            aggregate["base_sha"] == pull["base_sha"]
            and aggregate["tested_merge_sha"] == checkout["tested_sha"]
            and aggregate["tested_tree_sha"] == checkout["tested_tree"]
            and aggregate["head_tree_sha"] == checkout["head_tree"],
            "archive gate differs from the protected successful aggregate lineage",
        )
    artifact, checksum, receipt = artifact_receipt(
        api,
        args.workflow_run,
        args.workflow_attempt,
        pull,
        "PairedArchiveGate",
        "PairedArchiveGate.json",
    )
    origin = {
        **checkout,
        "repository": pull["repository"],
        "repository_id": pull["repository_id"],
        "pull_request": args.pull,
        "head_sha": revision,
        "base_sha": pull["base_sha"],
        "workflow": WORKFLOW,
        "run_id": args.workflow_run,
        "run_attempt": args.workflow_attempt,
        "job": "policy",
        "step": GATE_STEP,
    }
    collector = verify_receipt(
        api, receipt, origin, args.audited_revision, args.saves_sha256
    )
    aggregate_run = run_identity(api, args.aggregate_run, pull)
    if (
        pull_identity(api, args.pull) != pull
        or workflow_run(api, args.workflow_run, pull) != run
        or not latest_run(api, pull, run["workflow_id"], args.workflow_run, EVENT)
        or aggregate_run["run_attempt"] != args.aggregate_attempt
        or aggregate_run["status"] != "completed"
        or aggregate_run["conclusion"] != aggregate["aggregate_conclusion"]
        or not latest_run(api, pull, aggregate_run["workflow_id"], args.aggregate_run)
    ):
        return {**result, "status": "superseded"}
    return {
        **result,
        "status": "archive_gate_verified",
        "archive_gate": {
            "workflow_id": run["workflow_id"],
            "job_id": job,
            "artifact_id": artifact,
            "artifact_digest": checksum,
            "collector_blob": collector,
            "receipt_sha256": digest(receipt),
            "receipt": receipt,
        },
    }


def main(argv=None, client=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pull", required=True, type=int)
    parser.add_argument("--aggregate-run", required=True, type=int)
    parser.add_argument("--aggregate-attempt", required=True, type=int)
    parser.add_argument("--workflow-run", required=True, type=int)
    parser.add_argument("--workflow-attempt", required=True, type=int)
    parser.add_argument("--roster", required=True, type=Path)
    parser.add_argument("--roster-sha256", required=True)
    parser.add_argument("--audited-revision", required=True)
    parser.add_argument("--saves-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        require(
            min(
                args.pull,
                args.aggregate_run,
                args.aggregate_attempt,
                args.workflow_run,
                args.workflow_attempt,
            )
            > 0
            and sha(args.audited_revision, 40)
            and sha(args.saves_sha256, 64),
            "archive observation requires exact positive identifiers and audit pins",
        )
        if client is None:
            client = GitHubRead(
                args.repository,
                os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"),
            )
        print(canonical(observe(client, args)))
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        RecursionError,
        zipfile.BadZipFile,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as error:
        print(
            f"archive gate evidence refused ({type(error).__name__})", file=sys.stderr
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
