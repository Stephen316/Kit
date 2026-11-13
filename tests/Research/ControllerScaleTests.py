import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def CheckLargeQueue() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath)
        BatchFile = RootPath / "Batch.json"
        for Offset in range(0, 10000, 1000):
            _ = BatchFile.write_text(
                JsonCodec.dumps(
                    {
                        "jobs": [
                            {
                                "id": f"chain:{Index:05d}",
                                "kind": "fixture.inspect",
                                "inputs": {},
                                "depends_on": [f"chain:{Index-1:05d}"] if Index else [],
                                "rule_version": "rule@1",
                                "tool_version": "tool@1",
                            }
                            for Index in range(Offset, Offset + 1000)
                        ]
                    }
                ),
                encoding="utf-8",
            )
            assert (
                JsonCodec.loads(Client.RunCli("submit-batch", str(BatchFile)))[
                    "submitted"
                ]
                == 1000
            )
        assert (
            JsonCodec.loads(Client.RunCli("status", "--job", "chain:09999"))["jobs"][0][
                "state"
            ]
            == "waiting_evidence"
        )
        LeaseFile = RootPath / "Root.json"
        assert (
            JsonCodec.loads(
                Client.RunCli(
                    "claim", "--worker", "worker:root", "--claim-file", str(LeaseFile)
                )
            )["job"]
            == "chain:00000"
        )
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(LeaseFile),
            "--result",
            str(BatchFile),
            "--outcome",
            "completed",
            "--reason",
            "fixture root complete",
        )
        assert (
            JsonCodec.loads(
                Client.RunCli(
                    "claim",
                    "--worker",
                    "worker:next",
                    "--claim-file",
                    str(RootPath / "Next.json"),
                )
            )["job"]
            == "chain:00001"
        )
