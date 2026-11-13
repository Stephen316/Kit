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
        StatusInfo = JsonCodec.loads(Client.RunCli("status", "--job", "chain:09999"))
        assert StatusInfo["jobs"][0]["state"] == "waiting_evidence"
        assert StatusInfo["reconciled_jobs"] == 0
        ResultFile = RootPath / "Result.json"
        _ = ResultFile.write_text('{"fixture":true}', encoding="utf-8")
        for Index in range(250):
            LeaseFile = RootPath / f"Lease{Index}.json"
            assert (
                JsonCodec.loads(
                    Client.RunCli(
                        "claim",
                        "--worker",
                        "worker:chain",
                        "--claim-file",
                        str(LeaseFile),
                    )
                )["job"]
                == f"chain:{Index:05d}"
            )
            assert (
                JsonCodec.loads(Client.RunCli("heartbeat", "--lease", str(LeaseFile)))[
                    "reconciled_jobs"
                ]
                == 0
            )
            Finished = JsonCodec.loads(
                Client.RunCli(
                    "finish",
                    "--lease",
                    str(LeaseFile),
                    "--result",
                    str(ResultFile),
                    "--outcome",
                    "completed",
                    "--reason",
                    "fixture chain step",
                )
            )
            assert Finished["jobs"][0]["state"] == "completed"
            assert Finished["reconciled_jobs"] == 1
        assert (
            JsonCodec.loads(Client.RunCli("status", "--job", "chain:00250"))["jobs"][0][
                "state"
            ]
            == "queued"
        )
        assert (
            JsonCodec.loads(Client.RunCli("status", "--job", "chain:09999"))[
                "reconciled_jobs"
            ]
            == 0
        )
