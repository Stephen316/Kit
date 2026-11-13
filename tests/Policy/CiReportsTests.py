import os as SystemEnv
import subprocess as Subprocess
import tempfile as Tempfile
from pathlib import Path as FilePath

import pytest as Pytest


@Pytest.mark.parametrize(
    "CaseMode,CheckName",
    (
        ("status", "Ruff"),
        ("external", "Ruff"),
        ("unlisted-job", "Unlisted job"),
        ("unlisted-run", "Unlisted workflow"),
        ("check", "Ruff"),
        ("check", "Analyze (javascript-typescript)"),
        ("check", "Build and verify release artifacts"),
        ("check", "Label first-time contributors"),
    ),
)
def CheckReportFlow(CaseMode: str, CheckName: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    ScriptPath = RootPath / "tests/Policy/CiAggregation/RunAggregate.cjs"
    ExpectedPass = CaseMode != "check"
    with Tempfile.TemporaryDirectory() as TempPath:
        ResultInfo = Subprocess.run(
            ["node", str(ScriptPath), CaseMode, "failure", CheckName],
            cwd=RootPath,
            env={**SystemEnv.environ, "RUNNER_TEMP": TempPath},
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        EvidencePath = FilePath(TempPath) / "PrCiEvidence/Evidence.json"
        assert EvidencePath.exists() == ExpectedPass, ResultInfo.stderr
    assert ResultInfo.returncode == (0 if ExpectedPass else 1)
    assert "Review report" not in ResultInfo.stdout
    assert "Unlisted job" not in ResultInfo.stdout
    assert "Unlisted workflow" not in ResultInfo.stdout
    if ExpectedPass:
        assert "CI passed" in ResultInfo.stdout
        assert "Ruff" in ResultInfo.stdout
    else:
        assert f"CI failed: {CheckName}" in ResultInfo.stderr


@Pytest.mark.parametrize(
    "CaseMode,Reused,Reason",
    (
        ("squash", True, "Reusing healthy PR CI"),
        ("ancestor", True, "Reusing healthy PR CI"),
        ("unnamed", False, "No matching queued PR heads"),
        ("branch", False, "No matching queued PR heads"),
        ("tree", False, "Candidate tree or base differs from the tested PR inputs"),
        ("base", False, "Candidate tree or base differs from the tested PR inputs"),
    ),
)
def CheckQueueReuse(CaseMode: str, Reused: bool, Reason: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    ScriptPath = RootPath / "tests/Policy/CiAggregation/RunReuse.cjs"
    with Tempfile.TemporaryDirectory() as TempPath:
        ResultInfo = Subprocess.run(
            ["node", str(ScriptPath), CaseMode],
            cwd=RootPath,
            env={**SystemEnv.environ, "RUNNER_TEMP": TempPath},
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    assert ResultInfo.returncode == 0, ResultInfo.stderr
    assert f"reuse={str(Reused).lower()}" in ResultInfo.stdout, ResultInfo.stdout
    assert Reason in ResultInfo.stdout, ResultInfo.stdout
