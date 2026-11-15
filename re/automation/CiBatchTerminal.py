import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from CiBatch import require
from Records import canonical, digest, label, read_record

HOST = "api.github.com"
AGGREGATE = ".github/workflows/PullRequest.yml"
MAX_BYTES = 1024 * 1024
MEMBER_HASHES = {
    "fingerprint",
    "definition_sha256",
    "waiting_receipt_sha256",
    "waiting_result_sha256",
    "ci_input_sha256",
}


def sha(value, size):
    return (
        isinstance(value, str)
        and re.fullmatch(f"[0-9a-f]{{{size}}}", value) is not None
    )


class SecureRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, newurl):
        location = urlsplit(newurl)
        require(
            location.scheme == "https"
            and location.username is None
            and location.password is None,
            "GitHub redirect must use HTTPS without embedded credentials",
        )
        return super().redirect_request(request, file, code, message, headers, newurl)


class GitHubRead:
    def __init__(self, repository, token):
        require(
            re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9][A-Za-z0-9_.-]*", repository),
            "expected an exact GitHub repository name",
        )
        require(
            isinstance(token, str)
            and token
            and token.isascii()
            and not any(char.isspace() for char in token),
            "read-only GitHub authentication is required",
        )
        self.repository = repository
        self.token = token
        self.opener = build_opener(SecureRedirect())

    def get(self, path, archive=False):
        request = Request(
            f"https://{HOST}/repos/{self.repository}/{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        request.add_unredirected_header("Authorization", f"Bearer {self.token}")
        with self.opener.open(request, timeout=10) as response:
            location = urlsplit(response.geturl())
            require(
                location.scheme == "https" and (archive or location.netloc == HOST),
                "GitHub JSON must come from its official API",
            )
            raw = response.read(MAX_BYTES + 1)
        require(len(raw) <= MAX_BYTES, "GitHub response exceeds its byte limit")
        return raw

    def record(self, path):
        value = json.loads(self.get(path))
        require(isinstance(value, dict), "GitHub response must be a JSON object")
        return value


def load_roster(path, expected):
    value = checked_roster(read_record(path), expected)
    return value["batch_revision"], value["payload_sha256"]


def checked_roster(record, expected):
    value = dict(record)
    checksum = value.pop("payload_sha256", None)
    require(
        sha(expected, 64)
        and checksum == expected == digest(value)
        and set(value)
        == {"manifest_version", "scope", "batch_revision", "ci_role", "members"}
        and type(value["manifest_version"]) is int
        and value["manifest_version"] == 1
        and value["scope"] == "pending_ci_roster"
        and sha(value["batch_revision"], 40)
        and isinstance(value["members"], list)
        and 1 <= len(value["members"]) <= 64,
        "expected fixed pending CI roster provenance",
    )
    label(value["ci_role"])
    names = [member_name(member) for member in value["members"]]
    require(names == sorted(set(names)), "expected a unique canonical CI roster")
    return {**value, "payload_sha256": checksum}


def member_name(member):
    require(
        isinstance(member, dict)
        and set(member)
        == MEMBER_HASHES | {"job_id", "kind", "generation", "attempt", "ci_binding"}
        and all(sha(member[key], 64) for key in MEMBER_HASHES)
        and all(
            type(member[key]) is int and member[key] > 0
            for key in ("generation", "attempt")
        ),
        "pending CI roster member lacks exact waiting attempt identity",
    )
    label(member["kind"])
    label(member["ci_binding"])
    return label(member["job_id"])


def pull_identity(api, number):
    value = api.record(f"pulls/{number}")
    require(value["number"] == number, "GitHub returned a different pull request")
    return {
        "pull_number": number,
        "state": value["state"],
        "repository": value["base"]["repo"]["full_name"],
        "repository_id": value["base"]["repo"]["id"],
        "head_repository_id": value["head"]["repo"]["id"],
        "head_sha": value["head"]["sha"],
        "base_sha": value["base"]["sha"],
        "base_ref": value["base"]["ref"],
        "merge_sha": value["merge_commit_sha"],
    }


def run_identity(api, run_id, pull):
    run = api.record(f"actions/runs/{run_id}")
    require(
        run["id"] == run_id
        and run["repository"]["id"] == pull["repository_id"]
        and run["head_repository"]["id"] == pull["head_repository_id"]
        and run["head_sha"] == pull["head_sha"]
        and run["event"] == "pull_request_target"
        and run["path"].split("@", 1)[0] == AGGREGATE,
        "run does not belong to the trusted PR aggregate for this revision",
    )
    require(
        type(run["workflow_id"]) is int and run["workflow_id"] > 0,
        "aggregate run lacks its trusted workflow ID",
    )
    associated = run.get("pull_requests") or []
    require(
        not associated
        or any(row["number"] == pull["pull_number"] for row in associated),
        "aggregate run names a different pull request",
    )
    return {
        key: run[key] for key in ("workflow_id", "run_attempt", "status", "conclusion")
    }


def latest_run(api, pull, workflow, run_id, event="pull_request_target"):
    listing = api.record(
        f"actions/workflows/{workflow}/runs?head_sha={pull['head_sha']}&event={event}&per_page=100"
    )
    require(
        listing["total_count"] == len(listing["workflow_runs"]),
        "aggregate run listing is incomplete",
    )
    matched = [
        value["id"]
        for value in listing["workflow_runs"]
        if value["head_sha"] == pull["head_sha"]
        and value["event"] == event
        and value["workflow_id"] == workflow
        and (
            not value.get("pull_requests")
            or any(
                row["number"] == pull["pull_number"] for row in value["pull_requests"]
            )
        )
    ]
    return bool(matched) and max(matched) == run_id


def aggregate_job(api, run_id, attempt, head, conclusion):
    payload = api.record(f"actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100")
    require(
        payload["total_count"] == len(payload["jobs"]),
        "aggregate job listing is incomplete",
    )
    jobs = [job for job in payload["jobs"] if job["name"] == "CI Agg"]
    require(len(jobs) == 1, "expected one trusted CI aggregate job")
    job = jobs[0]
    require(
        job["run_id"] == run_id
        and job["run_attempt"] == attempt
        and job["head_sha"] == head
        and job["status"] == "completed"
        and job["conclusion"] == conclusion
        and type(job["id"]) is int
        and job["id"] > 0,
        "aggregate job does not match the terminal run attempt",
    )
    return job


def artifact_receipt(
    api,
    run_id,
    attempt,
    pull,
    artifact_name="PrCiEvidence",
    member_name="Evidence.json",
):
    listed = api.record(f"actions/runs/{run_id}/artifacts?per_page=100")
    require(
        listed["total_count"] == len(listed["artifacts"]),
        "aggregate artifact listing is incomplete",
    )
    artifacts = [
        value
        for value in listed["artifacts"]
        if value["name"] == f"{artifact_name}-{attempt}"
    ]
    require(
        len(artifacts) == 1,
        "expected the run attempt's immutable CI evidence artifact",
    )
    artifact = artifacts[0]
    identity = artifact["workflow_run"]
    checksum = artifact["digest"]
    require(
        artifact["expired"] is False
        and 0 < artifact["size_in_bytes"] <= MAX_BYTES
        and re.fullmatch("sha256:[0-9a-f]{64}", checksum)
        and identity["id"] == run_id
        and identity["repository_id"] == pull["repository_id"]
        and identity["head_repository_id"] == pull["head_repository_id"]
        and identity["head_sha"] == pull["head_sha"]
        and type(artifact["id"]) is int
        and artifact["id"] > 0,
        "evidence artifact is not bound to this repository and run",
    )
    content = api.get(f"actions/artifacts/{artifact['id']}/zip", archive=True)
    require(
        len(content) <= MAX_BYTES
        and checksum == "sha256:" + hashlib.sha256(content).hexdigest(),
        "CI evidence download failed its authenticated digest",
    )
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        entries = archive.infolist()
        require(
            len(entries) == 1
            and entries[0].filename == member_name
            and entries[0].file_size <= 65536,
            "unexpected CI evidence archive contents",
        )
        with archive.open(entries[0]) as source:
            raw = source.read(65537)
    require(len(raw) <= 65536, "CI evidence JSON exceeds its byte limit")
    evidence = json.loads(raw)
    require(isinstance(evidence, dict), "expected a CI evidence object")
    return artifact["id"], checksum, evidence


def verified_source(api, evidence, pull, run_id, attempt):
    expected = {
        key: pull[key]
        for key in (
            "repository_id",
            "head_repository_id",
            "pull_number",
            "head_sha",
            "base_sha",
        )
    }
    expected.update(
        format="pr-head-tree-v1",
        workflow_event="pull_request_target",
        report_merge_sha=pull["merge_sha"],
        run_id=run_id,
        run_attempt=attempt,
    )
    require(
        all(evidence.get(key) == value for key, value in expected.items())
        and sha(pull["merge_sha"], 40)
        and sha(evidence["head_tree_sha"], 40),
        "aggregate evidence differs from the exact PR, base or tested merge commit",
    )
    head = api.record(f"git/commits/{pull['head_sha']}")
    merge = api.record(f"git/commits/{pull['merge_sha']}")
    require(
        head["sha"] == pull["head_sha"]
        and head["tree"]["sha"] == evidence["head_tree_sha"]
        and merge["sha"] == pull["merge_sha"]
        and sha(merge["tree"]["sha"], 40)
        and sorted(parent["sha"] for parent in merge["parents"])
        == sorted((pull["base_sha"], pull["head_sha"])),
        "GitHub commit objects do not match the aggregate evidence ancestry",
    )
    return {
        "tested_merge_sha": pull["merge_sha"],
        "tested_tree_sha": merge["tree"]["sha"],
        "head_tree_sha": head["tree"]["sha"],
    }


def observe(api, repository, revision, roster_hash, pull_number, run_id, attempt):
    result = {
        "report_version": 1,
        "scope": "ci_batch_terminal_observation",
        "roster_payload_sha256": roster_hash,
        "batch_revision": revision,
        "repository": repository,
        "pull_number": pull_number,
        "run_id": run_id,
        "run_attempt": attempt,
        "member_attribution": "unavailable",
    }
    pull = pull_identity(api, pull_number)
    require(
        pull["repository"].casefold() == repository.casefold(),
        "pull request does not belong to the explicitly selected repository",
    )
    if pull["state"] != "open" or pull["head_sha"] != revision:
        return {**result, "status": "superseded"}
    run = run_identity(api, run_id, pull)
    if run["run_attempt"] != attempt or not latest_run(
        api, pull, run["workflow_id"], run_id
    ):
        return {**result, "status": "superseded"}
    if run["status"] != "completed":
        return {**result, "status": "pending"}
    require(
        run["conclusion"]
        in (
            "success",
            "failure",
            "cancelled",
            "timed_out",
            "action_required",
            "neutral",
            "skipped",
            "stale",
            "startup_failure",
        ),
        "aggregate run lacks a terminal conclusion",
    )
    job = aggregate_job(api, run_id, attempt, revision, run["conclusion"])
    observed = {
        **result,
        "aggregate_job_id": job["id"],
        "aggregate_conclusion": run["conclusion"],
        "status": "aggregate_failure_unattributed",
        "aggregate_source_binding": "head_only",
    }
    if run["conclusion"] == "success":
        require(
            any(
                step["name"] == "Verify the published evidence through GitHub"
                and step["status"] == "completed"
                and step["conclusion"] == "success"
                for step in job["steps"]
            ),
            "trusted aggregate did not verify its published evidence",
        )
        artifact_id, checksum, evidence = artifact_receipt(api, run_id, attempt, pull)
        observed.update(
            status="aggregate_success_attested",
            aggregate_source_binding="verified_pr_and_merge",
            evidence_artifact_id=artifact_id,
            evidence_artifact_digest=checksum,
            repository_id=pull["repository_id"],
            head_repository_id=pull["head_repository_id"],
            base_sha=pull["base_sha"],
            **verified_source(api, evidence, pull, run_id, attempt),
        )
    fresh = pull_identity(api, pull_number)
    if (
        fresh != pull
        or run_identity(api, run_id, fresh) != run
        or not latest_run(api, fresh, run["workflow_id"], run_id)
    ):
        return {**result, "status": "superseded"}
    return observed


def main(argv=None, client=None):
    parser = argparse.ArgumentParser(
        description="Observe the authenticated terminal CI aggregate for a frozen roster"
    )
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pull", type=int, required=True)
    parser.add_argument("--run", type=int, required=True)
    parser.add_argument("--run-attempt", type=int, required=True)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--roster-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        require(
            min(args.pull, args.run, args.run_attempt) > 0,
            "GitHub identifiers must be positive",
        )
        revision, checksum = load_roster(args.roster, args.roster_sha256)
        if client is None:
            client = GitHubRead(
                args.repository,
                os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"),
            )
        print(
            canonical(
                observe(
                    client,
                    args.repository,
                    revision,
                    checksum,
                    args.pull,
                    args.run,
                    args.run_attempt,
                )
            )
        )
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        RecursionError,
        zipfile.BadZipFile,
    ) as error:
        print(f"terminal CI evidence refused ({type(error).__name__})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
