import json as JsonCodec
import tempfile as TempFiles
from concurrent.futures import ThreadPoolExecutor as WorkerThreads
from pathlib import Path as FilePath

from tests.Research.ControllerPoolTests import PoolJob, WriteSchedule
from tests.Research.JobClient import JobClient


# simultaneous claimants must never start two copies of the same job
def CheckClaims() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath, 2)
        JobFile = RootPath / "Job.json"
        for Index in range(4):
            _ = JobFile.write_text(
                JsonCodec.dumps(
                    {
                        "id": f"job:{Index}",
                        "kind": "fixture.inspect",
                        "inputs": {},
                        "rule_version": "rule@1",
                        "tool_version": "tool@1",
                    }
                ),
                encoding="utf-8",
            )
            _ = Client.RunCli("submit", str(JobFile))
        with WorkerThreads(max_workers=8) as WorkerPool:
            Futures = [
                WorkerPool.submit(
                    Client.RunCli,
                    "claim",
                    "--worker",
                    f"worker:{Index}",
                    "--claim-file",
                    str(RootPath / f"Lease{Index}.json"),
                )
                for Index in range(8)
            ]
            Claimed = [JsonCodec.loads(Future.result())["job"] for Future in Futures]
        assert len([JobName for JobName in Claimed if JobName is not None]) == 2
        assert len({JobName for JobName in Claimed if JobName is not None}) == 2
        States = [
            JobInfo["state"]
            for JobInfo in JsonCodec.loads(Client.RunCli("status"))["jobs"]
        ]
        assert States.count("running") == 2
        assert States.count("queued") == 2


# successful group publication exposes the exact ordered lease roster
def ReadGroup(
    Client: JobClient,
    GroupPath: FilePath,
    RegistryFile: FilePath,
) -> list[str]:
    Response = JsonCodec.loads(
        Client.RunCli(
            "claim-group",
            "--worker",
            "worker:priority",
            "--pool",
            "decode",
            "--registry",
            str(RegistryFile),
            "--claim-dir",
            str(GroupPath),
        )
    )
    assert Response["count"] >= 2
    GroupInfo = JsonCodec.loads((GroupPath / "group.json").read_text(encoding="utf-8"))
    return [
        str(
            JsonCodec.loads((GroupPath / NameText).read_text(encoding="utf-8"))["job"][
                "id"
            ]
        )
        for NameText in GroupInfo["members"]
    ]


# equal evidence favors older jobs while rarer families keep their next turn
def CheckTurnOrder() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath, 4)
        _ = Client.RunCli("pool", "decode", "--kind", "fixture.decode")
        InputFile = RootPath / "Input.bin"
        _ = InputFile.write_bytes(b"ranked fixture input")
        _ = Client.RunCli("bind", "bound:fixture", str(InputFile))
        JobData = (
            ("rare:first", ["one"], ["variant"]),
            ("rare:second", ["one", "one"], ["variant"]),
            ("common:older", ["one", "two"], ["strong"]),
            ("common:strong", ["one", "two"], ["strong", "independent"]),
            ("common:also", ["one", "two"], ["strong"]),
            ("common:fourth", ["one", "two"], ["strong"]),
            ("common:fifth", ["one", "two"], ["strong"]),
            ("common:sixth", ["one", "two"], ["strong"]),
        )
        JobList = [
            PoolJob(JobName, "fixture.decode", inputs={"native": "bound:fixture"})
            for JobName, DocItems, EvidenceItems in JobData
        ]
        Ranks: list[dict[str, object]] = [
            {
                "id": JobName,
                "family": JobName.split(":")[0],
                "documents": DocItems,
                "distinguishing_evidence": EvidenceItems,
            }
            for JobName, DocItems, EvidenceItems in JobData
        ]
        PlanFile = WriteSchedule(RootPath / "Schedule.json", JobList, Ranks)
        _ = Client.RunCli("schedule", str(PlanFile))
        RegistryFile = RootPath / "Registry.json"
        _ = RegistryFile.write_text(
            JsonCodec.dumps(
                {"group_registry_version": 1, "kinds": {"fixture.decode": 8192}}
            ),
            encoding="utf-8",
        )
        CommonPath = RootPath / "Common"
        assert ReadGroup(Client, CommonPath, RegistryFile) == [
            "common:strong",
            "common:older",
            "common:also",
            "common:fourth",
        ]
        for LeaseName in ("00.json", "01.json"):
            _ = Client.RunCli(
                "finish",
                "--lease",
                str(CommonPath / LeaseName),
                "--result",
                str(PlanFile),
                "--outcome",
                "completed",
                "--reason",
                "decode observed",
            )
        assert ReadGroup(Client, RootPath / "Rare", RegistryFile) == [
            "rare:first",
            "rare:second",
        ]
