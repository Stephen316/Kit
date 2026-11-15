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


# archive checks combine authenticated job steps and evidence with an explicit audit pin
@TestMark.parametrize(
    ("CaseName", "Expected"),
    (
        ("success", "archive_gate_verified"),
        ("aggregate_failed", "archive_gate_verified"),
        ("job_failed_later", "archive_steps_verified_job_failed"),
        ("quality_other_live", "archive_gate_verified"),
        ("quality_rerun", "superseded"),
        ("wrong_audit", "refused"),
        ("wrong_source", "refused"),
        ("wrong_node", "refused"),
        ("wrong_step", "refused"),
        ("job_failed_before", "refused"),
        ("job_cancelled", "refused"),
        ("corrupt_zip", "refused"),
    ),
)
def CheckArchiveObs(TmpPath: FilePath, CaseName: str, Expected: str) -> None:
    ScriptPath = KRepoRoot / "re/automation/CiArchiveFixture.py"
    Process = Subprocess.run(
        [System.executable, str(ScriptPath), str(TmpPath), CaseName],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if Expected == "refused":
        assert Process.returncode == 1
        assert (
            Process.stdout == "" and "archive gate evidence refused" in Process.stderr
        )
        return
    assert Process.returncode == 0, Process.stderr
    Report = JsonCodec.loads(Process.stdout)
    assert Report["status"] == Expected
    assert Report["member_attribution"] == "unavailable"
    if Expected == "superseded":
        assert "archive_gate" not in Report
        return
    Evidence = Report["archive_gate"]
    assert Evidence["job_id"] == 5 and Evidence["artifact_id"] == 6
    JobConclusion = "failure" if CaseName == "job_failed_later" else "success"
    assert Evidence["job_conclusion"] == JobConclusion
    assert Evidence["artifact_digest"].startswith("sha256:")
    assert len(Evidence["receipt_sha256"]) == 64
    assert Evidence["receipt"]["origin"]["tested_sha"] == "3" * 40
    if CaseName in ("aggregate_failed", "job_failed_later", "quality_other_live"):
        assert Report["aggregate"]["status"] == "aggregate_failure_unattributed"
        assert "tested_merge_sha" not in Report["aggregate"]
    else:
        assert Report["aggregate"]["status"] == "aggregate_success_attested"
        assert Report["aggregate"]["tested_merge_sha"] == "3" * 40
