import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

from CiArchiveObservation import GATE_STEPS, JOB_NAME, WORKFLOW_NAME, main
from CiPairedArchiveGate import APPLICATIONS, CHECKS, COUNTS, GATE_STEP, ROOT, WORKFLOW
from CiTerminalFixture import BASE, HEAD, HEAD_TREE, MERGE, ReplyFixture, write_roster
from Corpus import git
from Records import digest


class ArchiveFixture(ReplyFixture):
    def __init__(self, case):
        super().__init__(
            "failed"
            if case in ("aggregate_failed", "job_failed_later", "quality_other_live")
            or case.startswith("gate_failed")
            and case != "gate_failed_green"
            else "success"
        )
        self.archive_case = case
        self.quality_runs = 0
        self.audit = git(ROOT, "rev-parse", "HEAD").decode("ascii").strip()
        self.tree = git(ROOT, "rev-parse", "HEAD^{tree}").decode("ascii").strip()
        self.url = "https://github.com/fixture/kit/actions/runs/4/job/5"
        saves = {
            family: {
                variant: {app: digest([family, variant, app]) for app in APPLICATIONS}
                for variant in (
                    "baseline-a",
                    "baseline-b",
                    *(f"fixture-{index}" for index in range(count - 2)),
                )
            }
            for family, count in COUNTS.items()
        }
        self.saves_sha = digest(saves)
        receipt = {
            "schema": 1,
            "scope": "hosted_paired_archive_gate",
            "origin": {
                "repository": "fixture/kit",
                "repository_id": 10,
                "pull_request": 94,
                "head_sha": HEAD,
                "head_tree": HEAD_TREE,
                "base_sha": BASE,
                "tested_sha": MERGE,
                "tested_tree": self.tree,
                "workflow": WORKFLOW,
                "workflow_ref": f"fixture/kit/{WORKFLOW}@refs/pull/94/merge",
                "workflow_sha": MERGE,
                "workflow_blob": self.blob(WORKFLOW),
                "run_id": 4,
                "run_attempt": 1,
                "job": "policy",
                "step": GATE_STEP,
            },
            "checks": [
                {
                    "nodeid": node,
                    "outcome": "passed",
                    "test_blob": self.blob(node.split("::", 1)[0]),
                }
                for node in CHECKS
            ],
            "corpus": {
                "capture_revision": "a" * 40,
                "specification_sha256": "b" * 64,
                "receipts": {
                    family: {app: digest([family, app]) for app in APPLICATIONS}
                    for family in COUNTS
                },
                "counts": COUNTS,
                "saves": saves,
                "saves_sha256": self.saves_sha,
            },
        }
        if case == "wrong_node":
            receipt["checks"][1]["nodeid"] += "Unexpected"
        content = io.BytesIO()
        with zipfile.ZipFile(content, "w") as archive:
            archive.writestr("PairedArchiveGate.json", json.dumps(receipt))
        self.archive_gate = content.getvalue()
        self.archive_digest = "sha256:" + hashlib.sha256(self.archive_gate).hexdigest()

    def blob(self, path):
        return git(ROOT, "rev-parse", f"{self.audit}:{path}").decode("ascii").strip()

    def quality(self):
        active = self.archive_case == "quality_other_live"
        return {
            "id": 4,
            "event": "pull_request",
            "path": WORKFLOW,
            "workflow_id": 31,
            "check_suite_id": 32,
            "head_sha": HEAD,
            "repository": {"id": 10},
            "head_repository": {"id": 20},
            "pull_requests": [],
            "run_attempt": 1,
            "status": "in_progress" if active else "completed",
            "conclusion": None if active else self.completed()["conclusion"],
        }

    def completed(self):
        conclusion = "success"
        if self.archive_case in (
            "job_failed_later",
            "job_failed_before",
        ) or self.archive_case.startswith("gate_failed"):
            conclusion = "failure"
        if self.archive_case == "job_cancelled":
            conclusion = "cancelled"
        return {
            "id": 5,
            "name": JOB_NAME,
            "head_sha": HEAD,
            "status": "completed",
            "conclusion": conclusion,
        }

    def record(self, path):
        if path == "actions/runs/4":
            self.quality_runs += 1
            result = self.quality()
            if (
                self.archive_case in ("quality_rerun", "gate_failed_rerun")
                and self.quality_runs > 1
            ):
                result["run_attempt"] = 2
            return result
        if path == "actions/workflows/31":
            return {"id": 31, "path": WORKFLOW}
        if (
            path
            == f"actions/workflows/31/runs?head_sha={HEAD}&event=pull_request&per_page=100"
        ):
            return {"total_count": 1, "workflow_runs": [self.quality()]}
        if path == "actions/runs/4/attempts/1/jobs?per_page=100":
            steps = [
                {
                    "name": name,
                    "number": number,
                    "status": "completed",
                    "conclusion": "success",
                }
                for number, name in enumerate(GATE_STEPS, 2)
            ]
            if self.archive_case == "wrong_step":
                steps[0]["conclusion"] = "skipped"
            if self.archive_case.startswith("gate_failed"):
                for number, step in enumerate(steps, 14):
                    step["number"] = number
                    step["conclusion"] = "failure" if number == 14 else "skipped"
            if self.archive_case == "gate_failed_upstream":
                steps.append(
                    {
                        "name": "Independent prerequisite",
                        "number": 13,
                        "status": "completed",
                        "conclusion": "failure",
                    }
                )
            if self.archive_case in ("job_failed_later", "job_failed_before"):
                number = (
                    len(GATE_STEPS) + 2
                    if self.archive_case == "job_failed_later"
                    else 1
                )
                steps.append(
                    {
                        "name": "Independent policy check",
                        "number": number,
                        "status": "completed",
                        "conclusion": "failure",
                    }
                )
            return {
                "total_count": 1,
                "jobs": [
                    {
                        **self.completed(),
                        "run_id": 4,
                        "run_attempt": 1,
                        "workflow_name": WORKFLOW_NAME,
                        "check_run_url": "https://api.github.com/repos/fixture/kit/check-runs/5",
                        "html_url": self.url,
                        "steps": steps,
                    }
                ],
            }
        if path == "check-runs/5":
            return {
                **self.completed(),
                "app": {"id": 15368},
                "check_suite": {"id": 32},
                "details_url": self.url,
            }
        if path == "actions/runs/4/artifacts?per_page=100":
            if self.archive_case.startswith("gate_failed"):
                raise AssertionError("a failed gate has no archive receipt to consult")
            return {
                "total_count": 1,
                "artifacts": [
                    {
                        "id": 6,
                        "name": "PairedArchiveGate-1",
                        "expired": False,
                        "size_in_bytes": len(self.archive_gate),
                        "digest": self.archive_digest,
                        "workflow_run": {
                            "id": 4,
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
            tree = "c" * 40 if self.archive_case == "wrong_audit" else self.tree
            return {
                "sha": MERGE,
                "tree": {"sha": tree},
                "parents": [{"sha": BASE}, {"sha": HEAD}],
            }
        if path.startswith("contents/") and path.endswith(f"?ref={MERGE}"):
            name = path.removeprefix("contents/").split("?", 1)[0]
            blob = self.blob(name)
            if (
                self.archive_case in ("wrong_source", "gate_failed_bad_source")
                and name == WORKFLOW
            ):
                blob = "d" * 40
            return {"path": name, "type": "file", "sha": blob}
        return super().record(path)

    def get(self, path, archive=False):
        if path == "actions/artifacts/6/zip" and archive:
            return self.archive_gate + (
                b"changed" if self.archive_case == "corrupt_zip" else b""
            )
        return super().get(path, archive)


def fixture(root, case):
    roster, roster_sha = write_roster(root)
    client = ArchiveFixture(case)
    return main(
        [
            "--repository",
            "fixture/kit",
            "--pull",
            "94",
            "--aggregate-run",
            "1",
            "--aggregate-attempt",
            "1",
            "--workflow-run",
            "4",
            "--workflow-attempt",
            "1",
            "--roster",
            str(roster),
            "--roster-sha256",
            roster_sha,
            "--audited-revision",
            client.audit,
            "--saves-sha256",
            client.saves_sha,
        ],
        client=client,
    )


if __name__ == "__main__":
    sys.exit(fixture(Path(sys.argv[1]), sys.argv[2]))
