"""Publish the exact hosted paired archive gate observation."""

import argparse
import json
import os
import re
from pathlib import Path

from Corpus import git
from PairedCaptureIntake import canonical_digest, recipe_roster, require

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ".github/workflows/WorkflowQuality.yml"
GATE_STEP = "Verify saved discovery evidence through both native archive readers"
CHECKS = (
    "tests/Research/Archives/ArchiveEvidenceTests.py::CheckArchive[paired-p01-p03-public-history]",
    "tests/Research/Archives/PairedCutHistoryTests.py::CheckCutHistory",
)
COUNTS = {"P01": 6, "P03": 8, "P04": 11}
APPLICATIONS = ("fusion", "solidworks")
PHASES = {"setup", "call", "teardown"}


def bounded_bytes(path, limit):
    with path.open("rb") as stream:
        content = stream.read(limit + 1)
    require(0 < len(content) <= limit, "invalid gate input size")
    return content


def commit(value):
    require(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value),
        "invalid Git commit identity",
    )
    return value


def provenance(environment):
    require(
        environment["GITHUB_EVENT_NAME"] == "pull_request"
        and environment["GITHUB_JOB"] == "policy"
        and environment["GITHUB_WORKFLOW"] == "Workflow quality"
        and environment["RUNNER_ENVIRONMENT"] == "github-hosted"
        and environment["RUNNER_OS"] == "Linux",
        "paired archive gate requires the hosted pull request policy job",
    )
    event = json.loads(
        bounded_bytes(Path(environment["GITHUB_EVENT_PATH"]), 2 * 1024 * 1024)
    )
    pull = event["pull_request"]
    number = event["number"]
    repo = pull["base"]["repo"]
    workflow_ref = environment["GITHUB_WORKFLOW_REF"]
    require(
        type(number) is int
        and number > 0
        and number == pull["number"]
        and repo["full_name"] == environment["GITHUB_REPOSITORY"]
        and str(repo["id"]) == environment["GITHUB_REPOSITORY_ID"]
        and environment["GITHUB_REF"] == f"refs/pull/{number}/merge"
        and workflow_ref.startswith(f"{repo['full_name']}/{WORKFLOW}@"),
        "paired archive gate repository or pull request identity differs",
    )
    tested = commit(environment["GITHUB_SHA"])
    workflow = commit(environment["GITHUB_WORKFLOW_SHA"])
    head, base = (commit(pull[side]["sha"]) for side in ("head", "base"))
    workflow_blob = git(ROOT, "rev-parse", f"HEAD:{WORKFLOW}")
    require(
        git(ROOT, "rev-list", "--parents", "-n", "1", "HEAD").decode("ascii").split()
        == [tested, base, head]
        and git(ROOT, "rev-parse", f"{workflow}:{WORKFLOW}") == workflow_blob
        and not git(
            ROOT,
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            WORKFLOW,
            "src",
            "re/automation",
            "re/Fusion/Study",
            "tests/Research/Archives",
        ),
        "paired archive gate checkout differs from the workflow and merge parents",
    )
    run = int(environment["GITHUB_RUN_ID"])
    attempt = int(environment["GITHUB_RUN_ATTEMPT"])
    require(run > 0 and attempt > 0, "invalid paired archive workflow run identity")
    return {
        "repository": repo["full_name"],
        "repository_id": repo["id"],
        "pull_request": number,
        "head_sha": head,
        "head_tree": git(ROOT, "rev-parse", f"{head}^{{tree}}").decode("ascii").strip(),
        "base_sha": base,
        "tested_sha": tested,
        "tested_tree": git(ROOT, "rev-parse", "HEAD^{tree}").decode("ascii").strip(),
        "workflow": WORKFLOW,
        "workflow_ref": workflow_ref,
        "workflow_sha": workflow,
        "workflow_blob": workflow_blob.decode("ascii").strip(),
        "run_id": run,
        "run_attempt": attempt,
        "job": "policy",
        "step": GATE_STEP,
    }


def passed_checks(path):
    phases = {node: set() for node in CHECKS}
    session_status = []
    for line in bounded_bytes(path, 4 * 1024 * 1024).splitlines():
        report = json.loads(line)
        report_type = report["$report_type"]
        if report_type == "SessionFinish":
            session_status.append(report["exitstatus"])
        if report_type != "TestReport" or report["nodeid"] not in phases:
            continue
        seen = phases[report["nodeid"]]
        phase = report["when"]
        require(
            phase in PHASES
            and phase not in seen
            and report["outcome"] == "passed"
            and "wasxfail" not in report,
            "paired archive check has a failed, skipped or repeated phase",
        )
        seen.add(phase)
    require(
        session_status == [0] and all(seen == PHASES for seen in phases.values()),
        "paired archive gate lacks a complete observed pass",
    )
    return [
        {
            "nodeid": node,
            "outcome": "passed",
            "test_blob": git(ROOT, "rev-parse", "HEAD:" + node.split("::", 1)[0])
            .decode("ascii")
            .strip(),
        }
        for node in CHECKS
    ]


def archive_roster():
    from P04FinalBodyEvidence import captures as cut_captures
    from RectanglePairEvidence import REVISION, SPECIFICATION_SHA256, capture

    snapshot, specification, fusion, solidworks = cut_captures()
    recipes = recipe_roster(specification)
    receipts, saves = {}, {}
    for family, count in COUNTS.items():
        by_application = (
            (fusion, solidworks)
            if family == "P04"
            else tuple(
                capture(snapshot, recipes[family], application, specification)[0]
                for application in APPLICATIONS
            )
        )
        pins = {}
        receipts[family] = {}
        for application, source in zip(APPLICATIONS, by_application, strict=True):
            require(
                source["recipe_id"] == family
                and source["application"] == application
                and source["split"] == "discovery",
                "unexpected paired archive capture identity",
            )
            receipts[family][application] = source["receipt"]["sha256"]
            pins[application] = {
                item["variant"]: item["sha256"] for item in source["native_files"]
            }
        require(
            pins["fusion"].keys() == pins["solidworks"].keys()
            and len(pins["fusion"]) == count
            and all(
                "baseline-a" in values
                and "baseline-b" in values
                and values["baseline-a"] != values["baseline-b"]
                for values in pins.values()
            ),
            "paired archive save roster or independent baselines differ",
        )
        saves[family] = {
            variant: {app: pins[app][variant] for app in APPLICATIONS}
            for variant in pins["fusion"]
        }
    return {
        "capture_revision": REVISION,
        "specification_sha256": SPECIFICATION_SHA256,
        "receipts": receipts,
        "counts": COUNTS,
        "saves": saves,
        "saves_sha256": canonical_digest(saves),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = {
        "schema": 1,
        "scope": "hosted_paired_archive_gate",
        "origin": provenance(os.environ),
        "checks": passed_checks(args.report_log),
        "corpus": archive_roster(),
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")


if __name__ == "__main__":
    main()
