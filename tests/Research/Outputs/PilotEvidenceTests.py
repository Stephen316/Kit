import hashlib as HashContent
import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient
from tests.Research.Outputs.PilotActivityTests import ReadActivity
from tests.Research.SupervisorClient import KRepoRoot


# each evidence source must remain distinct across replay and later controller activity
def CheckEvidence(TmpPath: FilePath) -> None:
    Client = JobClient(TmpPath)
    _ = Client.RunCli("resource", "fixture:initial", "--available")
    Activity = ReadActivity(
        TmpPath, ["--from-unix", "10", "--until-unix", str(TimeClock.time())]
    )
    Window = {
        Field: Activity[Field]
        for Field in (
            "from_unix_seconds",
            "until_unix_seconds",
            "after_event_id",
            "through_event_id",
            "selected_events_sha256",
        )
    }
    Missing = RunEvidence(TmpPath, Window, {})
    for Field in ("interventions", "agent_activity", "acceptance"):
        assert Missing[Field] == {"status": "unmeasured"}
    Sources = FixtureSources(TmpPath)
    Report = RunEvidence(TmpPath, Window, Sources)
    AssertEvidence(Report, Activity, Sources)
    _ = Client.RunCli("resource", "fixture:later", "--available")
    assert RunEvidence(TmpPath, Window, Sources) == Report
    AssertRefused(TmpPath, Window, Sources)


# changing either evidence cutoff content or stable record identity must refuse the report
def AssertRefused(
    RootPath: FilePath, Window: dict[str, object], Sources: dict[str, str]
) -> None:
    Changed = {**Window, "selected_events_sha256": "0" * 64}
    _ = RunEvidence(RootPath, Changed, Sources, ExitCode=1)
    IntervalPath = RootPath / "AgentIntervals.json"
    _ = IntervalPath.write_bytes(IntervalPath.read_bytes() + b" ")
    _ = RunEvidence(RootPath, Window, Sources, ExitCode=1)
    Records = Intervals()
    Updated = WritePinned(
        IntervalPath,
        {
            "version": 1,
            "authority": "measured_agent_intervals",
            "records": [*Records, {**Records[0], "until": 62}],
        },
    )
    _ = RunEvidence(
        RootPath, Window, {**Sources, "agent_activity": Updated}, ExitCode=1
    )


# report replay must read the actual controller store through the standalone command
def RunEvidence(
    RootPath: FilePath,
    Window: dict[str, object],
    Sources: dict[str, str],
    ExitCode: int = 0,
) -> dict[str, object]:
    ManifestPath = RootPath / "PilotEvidence.json"
    ManifestHash = WritePinned(
        ManifestPath, {"version": 1, "window": Window, "sources": Sources}
    )
    StorePath = RootPath / "State"
    DatabasePath = StorePath / "ledger.sqlite3"
    Before = DatabasePath.read_bytes()
    Result = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/PilotEvidence.py"),
            "--store",
            str(StorePath),
            "--manifest",
            str(ManifestPath),
            "--manifest-sha256",
            ManifestHash,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Result.returncode == ExitCode, Result.stderr
    assert DatabasePath.read_bytes() == Before
    Report: dict[str, object] = JsonCodec.loads(Result.stdout) if ExitCode == 0 else {}
    return Report


# the exact source digest must cover the serialized evidence supplied by its authority
def WritePinned(PathValue: FilePath, Record: dict[str, object]) -> str:
    Content = JsonCodec.dumps(Record, sort_keys=True).encode("utf-8")
    _ = PathValue.write_bytes(Content)
    return HashContent.sha256(Content).hexdigest()


# duplicate attestations and overlapping intervals must preserve their independent measures
def FixtureSources(RootPath: FilePath) -> dict[str, str]:
    Intervention = {
        "id": "response:known",
        "at": 12,
        "operator": "operator:one",
        "reason": "private explanatory note",
        "evidence_sha256": "0" * 64,
    }
    Before = {**Intervention, "id": "response:older", "at": 2}
    return {
        "interventions": WritePinned(
            RootPath / "Interventions.json",
            {
                "version": 1,
                "authority": "operator_attestation",
                "records": [Intervention, Intervention, Before],
            },
        ),
        "agent_activity": WritePinned(
            RootPath / "AgentIntervals.json",
            {
                "version": 1,
                "authority": "measured_agent_intervals",
                "records": Intervals(),
            },
        ),
        "acceptance": WritePinned(
            RootPath / "Acceptances.json",
            {
                "version": 1,
                "authority": "independent_acceptance_attestation",
                "records": AcceptedCases(),
            },
        ),
        "ci_activity": WritePinned(
            RootPath / "CiActivity.json",
            {
                "version": 1,
                "authority": "github_actions_job_observations",
                "records": CiJobs(),
            },
        ),
    }


# the pilot needs independent samples for wait before start and for job execution
def CiJobs() -> list[dict[str, object]]:
    RunPath = "https://api.github.com/repos/example/kit/actions"
    JobEntry: dict[str, object] = {
        "id": 201,
        "run_id": 11,
        "run_attempt": 2,
        "url": f"{RunPath}/jobs/201",
        "run_url": f"{RunPath}/runs/11",
        "head_sha": "a" * 40,
        "created_at": "1970-01-01T00:00:18Z",
        "started_at": "1970-01-01T00:00:24Z",
        "completed_at": "1970-01-01T00:00:32Z",
        "status": "completed",
        "conclusion": "success",
    }
    return [
        JobEntry,
        JobEntry,
        {
            **JobEntry,
            "id": 202,
            "url": f"{RunPath}/jobs/202",
            "conclusion": "skipped",
        },
        {
            **JobEntry,
            "id": 203,
            "url": f"{RunPath}/jobs/203",
            "created_at": None,
            "conclusion": "failure",
        },
        {
            **JobEntry,
            "id": 204,
            "url": f"{RunPath}/jobs/204",
            "completed_at": None,
            "conclusion": None,
            "status": "in_progress",
        },
    ]


# overlap and an open interval distinguish agent work time from elapsed active wall time
def Intervals() -> list[dict[str, object]]:
    First: dict[str, object] = {
        "id": "agent:one",
        "agent": "worker:a",
        "attempt": "fixture:attempt",
        "from": 5,
        "until": 20,
        "evidence_sha256": "a" * 64,
    }
    return [
        First,
        First,
        {**First, "id": "agent:two", "from": 15, "until": 26},
        {**First, "id": "agent:three", "agent": "worker:b", "from": 25, "until": 35},
        {**First, "id": "agent:open", "from": 32, "until": None},
    ]


# repeat acceptance across routes must preserve distinct cases and unique document gains
def AcceptedCases() -> list[dict[str, object]]:
    CaseInfo: dict[str, object] = {
        "id": "case:one",
        "document_sha256": "1" * 64,
        "at": 42,
        "family": "fixture",
        "format_version": "v1",
        "direction": "fixture:forward",
        "verifier": "fixture:oracle",
        "baseline": {"status": "not_accepted", "receipt_sha256": "b" * 64},
        "candidate": {"status": "accepted", "receipt_sha256": "c" * 64},
    }
    return [
        CaseInfo,
        CaseInfo,
        {**CaseInfo, "id": "case:two", "direction": "fixture:reverse"},
    ]


# a successful controller report may include independent evidence without disclosing its records
def AssertEvidence(
    Report: dict[str, object], Activity: dict[str, object], Sources: dict[str, str]
) -> None:
    assert Report["scope"] == "pre_pilot_operational_evidence"
    assert Report["controller_activity"] == Activity
    assert Report["interventions"] == {
        "status": "attested",
        "authority": "operator_attestation",
        "source_sha256": Sources["interventions"],
        "interventions": 1,
    }
    assert Report["agent_activity"] == {
        "status": "partial",
        "authority": "measured_agent_intervals",
        "source_sha256": Sources["agent_activity"],
        "closed_intervals": 3,
        "open_intervals": 1,
        "agent_seconds": 26,
        "active_wall_seconds": 25,
    }
    assert Report["acceptance"] == {
        "status": "independently_attested",
        "authority": "independent_acceptance_attestation",
        "source_sha256": Sources["acceptance"],
        "matched_cases": 2,
        "attested_case_gains": 2,
        "attested_document_gains": 1,
    }
    assert Report["ci_activity"] == {
        "status": "partial",
        "authority": "github_actions_job_observations",
        "source_sha256": Sources["ci_activity"],
        "conclusions": {"success": 1, "failure": 1, "skipped": 1},
        "unfinished_observations": 1,
        "pre_start_jobs": 1,
        "created_to_start_job_seconds": 6,
        "execution_timed_jobs": 2,
        "start_to_finish_job_seconds": 16,
    }
    assert "private explanatory note" not in JsonCodec.dumps(Report)
