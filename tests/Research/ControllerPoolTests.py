import json as JsonCodec
import subprocess as Subprocess
import tempfile as TempFiles
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def WriteJobs(RootPath: FilePath, JobList: list[dict[str, object]]) -> FilePath:
    BatchFile = RootPath / "Batch.json"
    _ = BatchFile.write_text(JsonCodec.dumps({"jobs": JobList}), encoding="utf-8")
    return BatchFile


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
