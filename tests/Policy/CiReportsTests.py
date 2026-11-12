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
