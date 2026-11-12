import json as JsonCodec
import os as SystemEnv
import subprocess as Subprocess
import tempfile as Tempfile
from pathlib import Path as FilePath

import pytest as Pytest

KRootPath = FilePath(__file__).resolve().parents[2]
KReviewers = JsonCodec.loads(
    (KRootPath / ".agents/skills/standard-pr-practice/ReviewBot.json").read_text()
)["Reviewers"]


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


@Pytest.mark.parametrize(
    "CaseMode,Verdict,PendingCheck",
    (
        ("queue", "pending", "Scorecard"),
        ("spoof", "success", "Ruff"),
        ("queue-missing", "success", "Merge queue acceptance"),
    ),
)
def TestPendingGate(CaseMode: str, Verdict: str, PendingCheck: str) -> None:
    ScriptPath = KRootPath / "tests/Policy/CiAggregation/RunAggregate.cjs"
    with Tempfile.TemporaryDirectory() as TempPath:
        with Pytest.raises(Subprocess.TimeoutExpired) as ErrorInfo:
            ResultInfo = Subprocess.run(
                ["node", str(ScriptPath), CaseMode, Verdict, PendingCheck],
                cwd=KRootPath,
                env={**SystemEnv.environ, "RUNNER_TEMP": TempPath},
                capture_output=True,
                check=False,
                timeout=2,
            )
            Pytest.fail(f"CI aggregate exited early with {ResultInfo.returncode}")
        assert f"Waiting for {PendingCheck}".encode() in (ErrorInfo.value.stdout or b"")
        assert not (FilePath(TempPath) / "PrCiEvidence/Evidence.json").exists()
