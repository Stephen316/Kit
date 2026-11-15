import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import KRepoRoot


# the disposable target and watcher are separate macos processes with real kernel exit events
@TestMark.skipif(
    System.platform != "darwin", reason="macOS exact process exit boundary"
)
@TestMark.parametrize(
    ("CaseName", "Expected"),
    (
        ("exit", "exact_exit_observed"),
        ("gone", "peer_unavailable"),
        ("mismatched", "refused"),
        ("timeout", "exit_unobserved"),
        ("replaced", "refused"),
        ("changed", "refused"),
    ),
)
def CheckExitWatch(TmpPath: FilePath, CaseName: str, Expected: str) -> None:
    ScriptPath = KRepoRoot / "re/automation/ApplicationWorkers/FusionExitFixture.py"
    RunResult = Subprocess.run(
        [
            System.executable,
            "-B",
            str(ScriptPath),
            "exercise",
            str(TmpPath.resolve()),
            CaseName,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=35,
    )
    assert RunResult.returncode == 0, RunResult.stderr
    Evidence = JsonCodec.loads(RunResult.stdout)
    assert Evidence["status"] == Expected
