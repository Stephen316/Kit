import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import KRepoRoot


# the compiled checkout bootstrap delivers the readiness event through a separate owned process
@TestMark.skipif(
    System.platform != "darwin", reason="macOS Fusion add-in dispatch boundary"
)
@TestMark.parametrize(
    ("CaseName", "Expected"),
    (
        ("accepted", "consumed"),
        ("open", "refused"),
        ("opened-later", "refused"),
        ("unlocked", "refused"),
        ("changed-fence", "refused"),
        ("expired", "refused"),
    ),
)
def CheckReadiness(TmpPath: FilePath, CaseName: str, Expected: str) -> None:
    ScriptPath = (
        KRepoRoot / "re/automation/ApplicationWorkers/FusionReadinessFixture.py"
    )
    RunResult = Subprocess.run(
        [System.executable, "-B", str(ScriptPath), str(TmpPath.resolve()), CaseName],
        capture_output=True,
        text=True,
        check=False,
        timeout=35,
    )
    assert RunResult.returncode == 0, RunResult.stderr
    Evidence = JsonCodec.loads(RunResult.stdout)
    assert Evidence["case"] == CaseName and Evidence["status"] == Expected
    assert Evidence["host"]["pid"] > 0


# the pinned addin callback and darwin watcher exercise the same one use action across processes
@TestMark.skipif(
    System.platform != "darwin", reason="macOS Fusion quit action boundary"
)
@TestMark.parametrize(
    ("CaseName", "Status", "ActionState", "Called"),
    (
        ("auto-exit", "exact_exit_observed", "reserved", True),
        ("auto-cancel", "exit_unobserved", "quit_call_returned", True),
        ("auto-uncertain", "exit_unobserved", "reserved", True),
        ("auto-open", "exit_unobserved", "refused", False),
        ("auto-after-reserve", "exit_unobserved", "refused", False),
        ("auto-fence", "exit_unobserved", "refused", False),
        ("auto-expired", "exit_unobserved", "request_pending", False),
    ),
)
def CheckArmedQuit(
    TmpPath: FilePath, CaseName: str, Status: str, ActionState: str, Called: bool
) -> None:
    ScriptPath = (
        KRepoRoot / "re/automation/ApplicationWorkers/FusionReadinessFixture.py"
    )
    RunResult = Subprocess.run(
        [System.executable, "-B", str(ScriptPath), str(TmpPath.resolve()), CaseName],
        capture_output=True,
        text=True,
        check=False,
        timeout=35,
    )
    assert RunResult.returncode == 0, RunResult.stderr
    Evidence = JsonCodec.loads(RunResult.stdout)
    assert Evidence["case"] == CaseName and Evidence["status"] == Status
    assert Evidence["called"] is Called
    assert Evidence["quit_action"]["state"] == ActionState
    assert ("receipt_sha256" in Evidence) is (CaseName == "auto-exit")
