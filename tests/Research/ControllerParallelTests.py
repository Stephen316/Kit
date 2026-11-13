import json as JsonCodec
import tempfile as TempFiles
from concurrent.futures import ThreadPoolExecutor as WorkerThreads
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


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
