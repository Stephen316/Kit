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
        ("startup", "aggregate_failure_unattributed"),
        ("startup_head_changed", "superseded"),
        ("startup_other_attempt", "refused"),
        ("startup_wrong_app", "refused"),
        ("startup_with_check", "refused"),
        ("startup_with_job", "refused"),
        ("failed_without_job", "refused"),
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
        AssertTermFail(Report, CaseName)


# startup observations need the suite identity because no job ran
def AssertTermFail(Report: dict[str, object], CaseName: str) -> None:
    assert Report["aggregate_source_binding"] == "head_only"
    if CaseName == "startup":
        assert Report["aggregate_conclusion"] == "startup_failure"
        assert Report["aggregate_terminal_event"] == "workflow_startup_failure"
        assert Report["aggregate_check_suite_id"] == 40
        assert "aggregate_job_id" not in Report
        assert "evidence_artifact_id" not in Report
    else:
        assert Report["aggregate_job_id"] == 2


# archive checks combine authenticated job steps and evidence with an explicit audit pin
@TestMark.parametrize(
    ("CaseName", "Expected"),
    (
        ("success", "archive_gate_verified"),
        ("aggregate_failed", "archive_gate_verified"),
        ("job_failed_later", "archive_steps_verified_job_failed"),
        ("gate_failed", "archive_gate_failed"),
        ("gate_failed_rerun", "superseded"),
        ("gate_failed_bad_source", "refused"),
        ("gate_failed_green", "refused"),
        ("gate_failed_upstream", "refused"),
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
        assert "archive_gate" not in Report and "archive_failure" not in Report
        return
    if Expected == "archive_gate_failed":
        AssertGateFail(Report)
        return
    AssertGatePass(Report, CaseName)


# successful gate observation requires the archive before aggregate lineage is considered
def AssertGatePass(Report: dict[str, object], CaseName: str) -> None:
    Evidence = JsonCodec.loads(JsonCodec.dumps(Report["archive_gate"]))
    Aggregate = JsonCodec.loads(JsonCodec.dumps(Report["aggregate"]))
    assert Evidence["job_id"] == 5 and Evidence["artifact_id"] == 6
    JobConclusion = "failure" if CaseName == "job_failed_later" else "success"
    assert Evidence["job_conclusion"] == JobConclusion
    assert Evidence["artifact_digest"].startswith("sha256:")
    assert len(Evidence["receipt_sha256"]) == 64
    assert Evidence["receipt"]["origin"]["tested_sha"] == "3" * 40
    if CaseName in ("aggregate_failed", "job_failed_later", "quality_other_live"):
        assert Aggregate["status"] == "aggregate_failure_unattributed"
        assert "tested_merge_sha" not in Aggregate
    else:
        assert Aggregate["status"] == "aggregate_success_attested"
        assert Aggregate["tested_merge_sha"] == "3" * 40


# failed step metadata can explain waiting without attesting to a member or receipt
def AssertGateFail(Report: dict[str, object]) -> None:
    assert "archive_gate" not in Report
    Failure = JsonCodec.loads(JsonCodec.dumps(Report["archive_failure"]))
    assert Failure["run_id"] == 4 and Failure["run_attempt"] == 1
    assert Failure["job_id"] == 5 and Failure["job_conclusion"] == "failure"
    assert (
        Failure["failed_step"]
        == "Verify saved discovery evidence through both native archive readers"
    )
    assert [
        (StepInfo["number"], StepInfo["conclusion"]) for StepInfo in Failure["steps"]
    ] == [
        (14, "failure"),
        (15, "skipped"),
        (16, "skipped"),
    ]
    assert Failure["audited_merge_candidate_sha"] == "3" * 40
    assert len(Failure["workflow_blob"]) == 40
    Aggregate = JsonCodec.loads(JsonCodec.dumps(Report["aggregate"]))
    assert Aggregate["status"] == "aggregate_failure_unattributed"
    assert "tested_merge_sha" not in Aggregate
