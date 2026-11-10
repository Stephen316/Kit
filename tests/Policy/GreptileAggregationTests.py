# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

import os as SystemEnv
import subprocess as Subprocess
import tempfile as Tempfile
from pathlib import Path as FilePath

import pytest as Pytest


@Pytest.mark.parametrize(
    "Verdict", ("success", "failure", "neutral", "skipped", "cancelled", "timed_out")
)
def TestPrReview(Verdict: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    ScriptPath = RootPath / "tests/Policy/CiAggregation/RunAggregate.cjs"
    with Tempfile.TemporaryDirectory() as TempPath:
        ResultInfo = Subprocess.run(
            ["node", str(ScriptPath), "greptile", Verdict],
            cwd=RootPath,
            env={**SystemEnv.environ, "RUNNER_TEMP": TempPath},
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        assert (FilePath(TempPath) / "PrCiEvidence/Evidence.json").exists() == (
            Verdict == "success"
        )
    assert ResultInfo.returncode == (
        0 if Verdict == "success" else 1
    ), ResultInfo.stderr
    assert ("CI passed" in ResultInfo.stdout) == (Verdict == "success")


@Pytest.mark.parametrize(
    "CaseMode,Verdict",
    (
        ("greptile", "pending"),
        ("greptile-stale", "success"),
        ("greptile-spoof", "success"),
        ("greptile-missing", "success"),
        ("queue", "pending"),
        ("queue-missing", "success"),
    ),
)
def TestPendingGate(CaseMode: str, Verdict: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    ScriptPath = RootPath / "tests/Policy/CiAggregation/RunAggregate.cjs"
    with Tempfile.TemporaryDirectory() as TempPath:
        with Pytest.raises(Subprocess.TimeoutExpired) as ErrorInfo:
            ResultInfo = Subprocess.run(
                ["node", str(ScriptPath), CaseMode, Verdict],
                cwd=RootPath,
                env={**SystemEnv.environ, "RUNNER_TEMP": TempPath},
                capture_output=True,
                check=False,
                timeout=2,
            )
            assert ResultInfo.returncode != 0
        assert b"CI passed" not in (ErrorInfo.value.stdout or b"")
        assert not (FilePath(TempPath) / "PrCiEvidence/Evidence.json").exists()
