import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.SupervisorClient import KRepoRoot


# terminal authority requires an exact archived receipt and a stable remote identity
@TestMark.parametrize(
    ("CaseName", "Expected"),
    (
        ("success", "aggregate_success_attested"),
        ("failed", "aggregate_failure_unattributed"),
        ("pending", "pending"),
        ("base_changed", "superseded"),
        ("head_changed", "superseded"),
        ("new_run", "superseded"),
        ("rerun", "superseded"),
        ("corrupt", "refused"),
        ("wrong_merge", "refused"),
        ("wrong_roster", "refused"),
    ),
)
def CheckCiObserve(TmpPath: FilePath, CaseName: str, Expected: str) -> None:
    ScriptPath = KRepoRoot / "re/automation/CiTerminalFixture.py"
    Process = Subprocess.run(
        [System.executable, str(ScriptPath), str(TmpPath), CaseName],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if Expected == "refused":
        assert Process.returncode == 1
        assert Process.stdout == "" and "terminal CI evidence refused" in Process.stderr
        return
    assert Process.returncode == 0, Process.stderr
    Report = JsonCodec.loads(Process.stdout)
    assert Report["status"] == Expected
    assert Report["member_attribution"] == "unavailable"
    assert Report["batch_revision"] == "1" * 40
    assert Report["pull_number"] == 94 and Report["run_id"] == 1
    assert Report["run_attempt"] == 1
    if Expected == "aggregate_success_attested":
        assert Report["tested_merge_sha"] == "3" * 40
        assert Report["tested_tree_sha"] == "5" * 40
        assert Report["evidence_artifact_id"] == 3
        assert Report["aggregate_source_binding"] == "verified_pr_and_merge"
    else:
        assert "tested_merge_sha" not in Report
    if Expected == "aggregate_failure_unattributed":
        assert Report["aggregate_source_binding"] == "head_only"
