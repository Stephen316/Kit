# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

import os as SystemEnv
import subprocess as Subprocess
import tempfile as Tempfile
from pathlib import Path as FilePath

import pytest as Pytest


@Pytest.mark.parametrize("Verdict", ("pending", "neutral", "failure", "success"))
@Pytest.mark.parametrize("CaseMode", ("reviews", "check", "status", "external"))
def CheckReportFlow(CaseMode: str, Verdict: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    ScriptPath = RootPath / "tests/Policy/CiAggregation/RunAggregate.cjs"
    with Tempfile.TemporaryDirectory() as TempPath:
        ResultInfo = Subprocess.run(
            ["node", str(ScriptPath), CaseMode, Verdict],
            cwd=RootPath,
            env={**SystemEnv.environ, "RUNNER_TEMP": TempPath},
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        EvidencePath = FilePath(TempPath) / "PrCiEvidence/Evidence.json"
        assert EvidencePath.exists() == (CaseMode == "reviews"), ResultInfo.stderr
    assert ResultInfo.returncode == (0 if CaseMode == "reviews" else 1)
    assert "Review report" not in ResultInfo.stdout
    assert "review-" not in ResultInfo.stdout
    if CaseMode == "reviews":
        assert "CI passed" in ResultInfo.stdout
        assert "Ruff" in ResultInfo.stdout
    else:
        assert "CI failed" in ResultInfo.stderr
