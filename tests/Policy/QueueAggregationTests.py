import os as SystemEnv
import subprocess as Subprocess
import tempfile as Tempfile
from pathlib import Path as FilePath

import pytest as Pytest


@Pytest.mark.parametrize(
    "CheckName", ("Scorecard", "dlint", "Analyze python", "Run the complete test suite")
)
@Pytest.mark.parametrize(
    "Verdict", ("success", "failure", "neutral", "skipped", "cancelled", "timed_out")
)
@Pytest.mark.parametrize("CaseMode", ("queue", "queue-run"))
def TestQueueGate(CheckName: str, Verdict: str, CaseMode: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    ScriptPath = RootPath / "tests/Policy/CiAggregation/RunAggregate.cjs"
    with Tempfile.TemporaryDirectory() as TempPath:
        ResultInfo = Subprocess.run(
            ["node", str(ScriptPath), CaseMode, Verdict, CheckName],
            cwd=RootPath,
            env={**SystemEnv.environ, "RUNNER_TEMP": TempPath},
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        assert not (FilePath(TempPath) / "PrCiEvidence/Evidence.json").exists()
    assert ResultInfo.returncode == (
        0 if Verdict == "success" else 1
    ), ResultInfo.stderr
    assert ("CI passed" in ResultInfo.stdout) == (Verdict == "success")
    if Verdict != "success":
        assert "CI failed" in ResultInfo.stderr
