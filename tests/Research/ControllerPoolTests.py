import json as JsonCodec
import subprocess as Subprocess
import tempfile as TempFiles
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


# pool scenarios exercise batch intake through the same file contract as production
def WriteJobs(RootPath: FilePath, JobList: list[dict[str, object]]) -> FilePath:
    BatchFile = RootPath / "Batch.json"
    _ = BatchFile.write_text(JsonCodec.dumps({"jobs": JobList}), encoding="utf-8")
    return BatchFile


# shared fixture defaults let each capacity case identify only the scheduling fields it varies
def PoolJob(JobName: str, KindName: str, **Settings: object) -> dict[str, object]:
    JobInfo: dict[str, object] = {
        "id": JobName,
        "kind": KindName,
        "inputs": {},
        "rule_version": "rule@1",
        "tool_version": "tool@1",
    }
    JobInfo.update(Settings)
    return JobInfo


# tests compare claimed work across selectors without depending on unrelated lease metadata
def ClaimName(Client: JobClient, ClaimFile: FilePath, *ArgItems: str) -> object:
    return JsonCodec.loads(
        Client.RunCli(
            "claim",
            "--worker",
            "worker:pool",
            "--claim-file",
            str(ClaimFile),
            *ArgItems,
        )
    )["job"]


# admitting work must respect each configured pool capacity during concurrent operation
def CheckCapacity() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath, 8)
        _ = Client.RunCli(
            "submit-batch",
            str(
                WriteJobs(
                    RootPath,
                    [
                        PoolJob(
                            f"provider:{Index}",
                            "fixture.model",
                            resources=["provider:fixture"],
                        )
                        for Index in range(3)
                    ],
                )
            ),
        )
        Created = JsonCodec.loads(
            Client.RunCli("resource", "provider:fixture", "--capacity", "2")
        )
        assert Created == {
            "available": False,
            "capacity": 2,
            "name": "provider:fixture",
        }
        assert ClaimName(Client, RootPath / "Early.json") is None
        _ = Client.RunCli("resource", "provider:fixture", "--available")
        assert ClaimName(Client, RootPath / "First.json") == "provider:0"
        assert ClaimName(Client, RootPath / "Second.json") == "provider:1"
        assert ClaimName(Client, RootPath / "Third.json") is None
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(RootPath / "First.json"),
            "--result",
            str(RootPath / "Batch.json"),
            "--outcome",
            "completed",
            "--reason",
            "fixture complete",
        )
        _ = Client.RunCli("resource", "provider:fixture", "--capacity", "1")
        assert ClaimName(Client, RootPath / "Fourth.json") is None
        _ = Client.RunCli("resource", "provider:fixture", "--capacity", "2")
        assert ClaimName(Client, RootPath / "Fifth.json") == "provider:2"
        _ = Client.RunCli(
            "resource", "provider:fixture", "--capacity", "65", ExitCode=1
        )
        _ = Client.RunCli("resource", "provider:fixture", ExitCode=1)


# selectors must keep workers from consuming jobs assigned to other pools
def CheckPoolClaims() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath, 8)
        _ = Client.RunCli(
            "submit-batch",
            str(
                WriteJobs(
                    RootPath,
                    [
                        PoolJob("model:first", "fixture.model"),
                        PoolJob("decode:first", "fixture.decode"),
                        PoolJob("decode:second", "fixture.decode"),
                    ],
                )
            ),
        )
        _ = Client.RunCli(
            "claim",
            "--worker",
            "worker:pool",
            "--pool",
            "decode",
            "--claim-file",
            str(RootPath / "Missing.json"),
            ExitCode=1,
        )
        Defined = JsonCodec.loads(
            Client.RunCli("pool", "decode", "--kind", "fixture.decode")
        )
        assert Defined == {"kinds": ["fixture.decode"], "pool": "decode"}
        _ = Client.RunCli("pool", "model", "--kind", "fixture.decode", ExitCode=1)
        _ = Client.RunCli("pool", "model", "--kind", "fixture.model")
        DecodeArgs = ("--pool", "decode")
        assert ClaimName(Client, RootPath / "A.json", *DecodeArgs) == "decode:first"
        assert ClaimName(Client, RootPath / "B.json", *DecodeArgs) == "decode:second"
        assert ClaimName(Client, RootPath / "C.json", *DecodeArgs) is None
        assert (
            ClaimName(Client, RootPath / "D.json", "--pool", "model") == "model:first"
        )
        Status = JsonCodec.loads(Client.RunCli("status"))
        assert {JobRow["id"]: JobRow["kind"] for JobRow in Status["jobs"]} == {
            "decode:first": "fixture.decode",
            "decode:second": "fixture.decode",
            "model:first": "fixture.model",
        }


# a stale pool claimant must remain fenced even when another worker can claim the same job
def CheckFencing() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath, 8)
        EvidenceFile = RootPath / "Evidence.bin"
        _ = EvidenceFile.write_bytes(b"first")
        _ = Client.RunCli("bind", "evidence:fixture", str(EvidenceFile))
        _ = Client.RunCli(
            "submit-batch",
            str(
                WriteJobs(
                    RootPath,
                    [
                        PoolJob(
                            "stale:inputs",
                            "fixture.decode",
                            inputs={"evidence": "evidence:fixture"},
                        ),
                        PoolJob(
                            "stale:expired",
                            "fixture.decode",
                            lease_seconds=1,
                            timeout_seconds=1,
                        ),
                    ],
                )
            ),
        )
        InputLease = RootPath / "Inputs.json"
        ExpiredLease = RootPath / "Expired.json"
        assert ClaimName(Client, InputLease) == "stale:inputs"
        assert ClaimName(Client, ExpiredLease) == "stale:expired"
        _ = Client.RunCli("heartbeat", "--lease", str(InputLease))
        _ = EvidenceFile.write_bytes(b"second")
        _ = Client.RunCli("bind", "evidence:fixture", str(EvidenceFile))
        Refused = Subprocess.run(
            Client.Command + ["heartbeat", "--lease", str(InputLease)],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert Refused.returncode == 3, Refused.stderr
        assert "inputs changed" in Refused.stderr or "revoked" in Refused.stderr
        FinishArgs = [
            "--result",
            str(EvidenceFile),
            "--outcome",
            "completed",
            "--reason",
            "late fixture result",
        ]
        _ = Client.RunCli("finish", "--lease", str(InputLease), *FinishArgs, ExitCode=3)
        TimeClock.sleep(1.2)
        _ = Client.RunCli(
            "finish", "--lease", str(ExpiredLease), *FinishArgs, ExitCode=3
        )
        _ = Client.RunCli("heartbeat", "--lease", str(ExpiredLease), ExitCode=3)
        Requeued = JsonCodec.loads(Client.RunCli("status", "--job", "stale:inputs"))
        assert Requeued["jobs"][0]["state"] == "queued"
        assert Requeued["jobs"][0]["generation"] == 2


# process scenarios share the scheduler file contract
def WriteSchedule(
    ScheduleFile: FilePath,
    JobList: list[dict[str, object]],
    RankRows: list[dict[str, object]],
) -> FilePath:
    _ = ScheduleFile.write_text(
        JsonCodec.dumps({"schedule_version": 1, "jobs": JobList, "priority": RankRows}),
        encoding="utf-8",
    )
    return ScheduleFile


# grid admission must replenish standard work and preserve live claims and decode prerequisites
def CheckGridQueue() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath, 4)
        InstallName = "application:fixture"
        AppKind = "fixture.grid"
        _ = Client.RunCli("resource", InstallName, "--available", "--capacity", "1")
        _ = Client.RunCli("pool", "application", "--kind", AppKind)
        _ = Client.RunCli("pool", "decode", "--kind", "fixture.decode")
        GridNames = ["grid:request-a", "grid:request-b"]
        GridNames.extend(f"grid:standard-{Index:02d}" for Index in range(11))
        GridSpecs = [
            PoolJob(GridName, AppKind, resources=[InstallName])
            for GridName in GridNames
        ]
        GridRanks: list[dict[str, object]] = [
            {
                "id": GridName,
                "family": "rectangle",
                "documents": ["reference"],
                "distinguishing_evidence": ["direction"],
                "grid": "requested" if Index < 2 else "standard",
                "installation": InstallName,
            }
            for Index, GridName in enumerate(GridNames)
        ]
        GridRanks[1]["documents"] = ["one", "two", "three"]
        DecodeSpec = PoolJob(
            "decode:after-grid",
            "fixture.decode",
            depends_on=["grid:request-a"],
            inputs={"grid": {"dependency": "grid:request-a"}},
        )
        DecodeRank: dict[str, object] = {
            "id": "decode:after-grid",
            "family": "rectangle",
            "documents": ["reference"],
            "distinguishing_evidence": [],
        }
        PlanFile = WriteSchedule(
            RootPath / "Schedule.json",
            GridSpecs + [DecodeSpec],
            GridRanks + [DecodeRank],
        )
        Initial = JsonCodec.loads(Client.RunCli("schedule", str(PlanFile)))
        assert Initial["queued_by_installation"] == {InstallName: 10}
        assert Initial["deferred_standard"] == 3
        assert ClaimName(Client, RootPath / "Blocked.json", "--pool", "decode") is None
        FirstFile = RootPath / "First.json"
        assert ClaimName(Client, FirstFile, "--pool", "application") == "grid:request-a"
        NewlyQueued = JsonCodec.loads(
            Client.RunCli("status", "--job", "grid:standard-08")
        )
        assert NewlyQueued["jobs"][0]["state"] == "queued"
        assert (
            ClaimName(Client, RootPath / "Busy.json", "--pool", "application") is None
        )

        GridRanks[0]["distinguishing_evidence"] = ["changed-priority"]
        PlanFile = WriteSchedule(
            RootPath / "Refresh.json", GridSpecs[:1], GridRanks[:1]
        )
        _ = Client.RunCli("schedule", str(PlanFile))
        _ = Client.RunCli("heartbeat", "--lease", str(FirstFile))
        GridSpecs[0]["rule_version"] = "rule@2"
        PlanFile = WriteSchedule(
            RootPath / "Conflict.json", GridSpecs[:1], GridRanks[:1]
        )
        _ = Client.RunCli("schedule", str(PlanFile), ExitCode=1)
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(FirstFile),
            "--result",
            str(PlanFile),
            "--outcome",
            "completed",
            "--reason",
            "grid observed",
        )
        assert (
            ClaimName(Client, RootPath / "Decode.json", "--pool", "decode")
            == "decode:after-grid"
        )
        SecondFile = RootPath / "Second.json"
        assert (
            ClaimName(Client, SecondFile, "--pool", "application") == "grid:request-b"
        )
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(SecondFile),
            "--result",
            str(PlanFile),
            "--outcome",
            "completed",
            "--reason",
            "grid observed",
        )
        assert (
            ClaimName(Client, RootPath / "Standard.json", "--pool", "application")
            == "grid:standard-00"
        )
