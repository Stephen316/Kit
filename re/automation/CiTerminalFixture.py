import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

from CiBatchTerminal import main
from Records import digest

HEAD = "1" * 40
BASE = "2" * 40
MERGE = "3" * 40
HEAD_TREE = "4" * 40
MERGE_TREE = "5" * 40


class ReplyFixture:
    def __init__(self, case):
        self.case = case
        self.pulls = self.runs = self.listings = 0
        self.conclusion = "failure" if case == "failed" else "success"
        evidence = {
            "format": "pr-head-tree-v1",
            "workflow_event": "pull_request_target",
            "repository_id": 10,
            "head_repository_id": 20,
            "pull_number": 94,
            "head_sha": HEAD,
            "base_sha": BASE,
            "head_tree_sha": HEAD_TREE,
            "report_merge_sha": MERGE,
            "run_id": 1,
            "run_attempt": 1,
        }
        content = io.BytesIO()
        with zipfile.ZipFile(content, "w") as archive:
            archive.writestr("Evidence.json", json.dumps(evidence))
        self.archive = content.getvalue()
        self.checksum = "sha256:" + hashlib.sha256(self.archive).hexdigest()

    def record(self, path):
        if path == "pulls/94":
            self.pulls += 1
            base = "6" * 40 if self.case == "base_changed" and self.pulls > 1 else BASE
            head = "7" * 40 if self.case == "head_changed" and self.pulls > 1 else HEAD
            return {
                "number": 94,
                "state": "open",
                "merge_commit_sha": MERGE,
                "base": {
                    "repo": {"id": 10, "full_name": "fixture/kit"},
                    "sha": base,
                    "ref": "main",
                },
                "head": {"repo": {"id": 20}, "sha": head},
            }
        if path == "actions/runs/1":
            self.runs += 1
            attempt = 2 if self.case == "rerun" and self.runs > 1 else 1
            done = self.case != "pending"
            return {
                **self.run_summary(1),
                "run_attempt": attempt,
                "status": "completed" if done else "in_progress",
                "conclusion": self.conclusion if done else None,
                "repository": {"id": 10},
                "head_repository": {"id": 20},
                "path": ".github/workflows/PullRequest.yml",
            }
        if (
            path
            == f"actions/workflows/30/runs?head_sha={HEAD}&event=pull_request_target&per_page=100"
        ):
            self.listings += 1
            runs = [self.run_summary(1)]
            if self.case == "new_run" and self.listings > 1:
                runs.append(self.run_summary(2))
            return {"total_count": len(runs), "workflow_runs": runs}
        if path == "actions/runs/1/attempts/1/jobs?per_page=100":
            return {
                "total_count": 1,
                "jobs": [
                    {
                        "id": 2,
                        "name": "CI Agg",
                        "run_id": 1,
                        "run_attempt": 1,
                        "head_sha": HEAD,
                        "status": "completed",
                        "conclusion": self.conclusion,
                        "steps": [
                            {
                                "name": "Verify the published evidence through GitHub",
                                "status": "completed",
                                "conclusion": self.conclusion,
                            }
                        ],
                    }
                ],
            }
        if self.conclusion == "failure":
            raise AssertionError("failed aggregate cannot supply success evidence")
        if path == "actions/runs/1/artifacts?per_page=100":
            return {
                "total_count": 1,
                "artifacts": [
                    {
                        "id": 3,
                        "name": "PrCiEvidence-1",
                        "expired": False,
                        "size_in_bytes": len(self.archive),
                        "digest": self.checksum,
                        "workflow_run": {
                            "id": 1,
                            "head_sha": HEAD,
                            "repository_id": 10,
                            "head_repository_id": 20,
                        },
                    }
                ],
            }
        if path == f"git/commits/{HEAD}":
            return {"sha": HEAD, "tree": {"sha": HEAD_TREE}}
        if path == f"git/commits/{MERGE}":
            tip = "8" * 40 if self.case == "wrong_merge" else HEAD
            return {
                "sha": MERGE,
                "tree": {"sha": MERGE_TREE},
                "parents": [{"sha": BASE}, {"sha": tip}],
            }
        raise AssertionError("unexpected GitHub record request")

    def run_summary(self, run_id):
        return {
            "id": run_id,
            "head_sha": HEAD,
            "event": "pull_request_target",
            "workflow_id": 30,
        }

    def get(self, path, archive=False):
        assert path == "actions/artifacts/3/zip" and archive
        return self.archive + b"changed" if self.case == "corrupt" else self.archive


def fixture(root, case):
    body = {
        "manifest_version": 1,
        "scope": "pending_ci_roster",
        "batch_revision": HEAD,
        "ci_role": "ci",
        "members": [
            {
                "job_id": "fixture:waiting",
                "kind": "fixture.verify",
                "generation": 1,
                "attempt": 1,
                "ci_binding": "ci:fixture",
                "fingerprint": "a" * 64,
                "definition_sha256": "b" * 64,
                "waiting_receipt_sha256": "c" * 64,
                "waiting_result_sha256": "d" * 64,
                "ci_input_sha256": "e" * 64,
            }
        ],
    }
    checksum = digest(body)
    roster = root / "Roster.json"
    roster.write_text(
        json.dumps({**body, "payload_sha256": checksum}), encoding="utf-8"
    )
    expected = "0" * 64 if case == "wrong_roster" else checksum
    return main(
        [
            "--repository",
            "fixture/kit",
            "--pull",
            "94",
            "--run",
            "1",
            "--run-attempt",
            "1",
            "--roster",
            str(roster),
            "--roster-sha256",
            expected,
        ],
        client=ReplyFixture(case),
    )


if __name__ == "__main__":
    sys.exit(fixture(Path(sys.argv[1]), sys.argv[2]))
