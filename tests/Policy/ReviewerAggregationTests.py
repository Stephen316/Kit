import json as JsonCodec
import os as SystemEnv
import subprocess as Subprocess
import tempfile as Tempfile
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Policy.WaitPending import WaitPending

# root path needs a stable location so repository automation resolves inputs independently of the caller working directory
KRootPath = FilePath(__file__).resolve().parents[2]

# the reviewers cases must remain explicit so repository automation exercises the intended compatibility boundary
KReviewers = JsonCodec.loads(
    (KRootPath / ".agents/skills/standard-pr-practice/ReviewBot.json").read_text()
)["Reviewers"]


# the review skip contract needs boundary coverage so the real command boundary enforces repository contracts
@Pytest.mark.parametrize(
    "Verdict",
    (
        "missing",
        "pending",
        "success",
        "failure",
        "neutral",
        "skipped",
        "cancelled",
        "timed_out",
    ),
)
@Pytest.mark.parametrize("CaseMode", ("reviews", "queue-reviews"))
def TestReviewSkip(Verdict: str, CaseMode: str) -> None:
    ScriptPath = KRootPath / "tests/Policy/CiAggregation/RunAggregate.cjs"
    with Tempfile.TemporaryDirectory() as TempPath:
        ResultInfo = Subprocess.run(
            ["node", str(ScriptPath), CaseMode, Verdict],
            cwd=KRootPath,
            env={**SystemEnv.environ, "RUNNER_TEMP": TempPath},
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        EvidencePath = FilePath(TempPath) / "PrCiEvidence/Evidence.json"
        assert EvidencePath.exists() == (CaseMode == "reviews"), ResultInfo.stderr
    assert ResultInfo.returncode == 0, ResultInfo.stderr
    assert "CI passed" in ResultInfo.stdout
    for Reviewer in KReviewers:
        for ReportName in Reviewer["Checks"] + Reviewer["Statuses"]:
            assert ReportName not in ResultInfo.stdout


# pending evidence must remain unpublished while required checks are still unresolved
@Pytest.mark.parametrize(
    "CaseMode,Verdict,PendingCheck",
    (
        ("queue", "pending", "Scorecard"),
        ("spoof", "success", "Ruff"),
        ("queue-missing", "success", "Merge queue acceptance"),
        ("quality-missing", "success", "Code Quality"),
        ("quality-empty", "success", "Code Quality analysis"),
    ),
)
def TestPendingGate(CaseMode: str, Verdict: str, PendingCheck: str) -> None:
    ScriptPath = KRootPath / "tests/Policy/CiAggregation/RunAggregate.cjs"
    with Tempfile.TemporaryDirectory() as TempPath:
        WaitPending(
            ["node", str(ScriptPath), CaseMode, Verdict, PendingCheck],
            KRootPath,
            {**SystemEnv.environ, "RUNNER_TEMP": TempPath},
            PendingCheck,
        )
        assert not (FilePath(TempPath) / "PrCiEvidence/Evidence.json").exists()
