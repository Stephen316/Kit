import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient
from tests.Research.SupervisorClient import FixtureJob


# queue growth must preserve usable controller state beyond the size of the small fixtures
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


# an observer must recover every committed event in its window while new work continues to append
def CheckEventPage(TmpPath: FilePath) -> None:
    Client = JobClient(TmpPath)
    Empty = JsonCodec.loads(Client.RunCli("events", "--after", "0"))
    assert Empty == {"events": [], "after": 0, "through": 0, "next_after": None}
    BatchPath = TmpPath / "EventJobs.json"
    JobValues = [
        FixtureJob(f"observe:{Index}", "fixture.inspect") for Index in range(101)
    ]
    _ = BatchPath.write_text(JsonCodec.dumps({"jobs": JobValues}), encoding="utf-8")
    _ = Client.RunCli("submit-batch", str(BatchPath))
    PageInfo = JsonCodec.loads(Client.RunCli("events", "--after", "0"))
    Through = PageInfo["through"]
    assert len(PageInfo["events"]) == 100 and PageInfo["next_after"] == 100
    Recent = JsonCodec.loads(Client.RunCli("events"))
    assert set(Recent) == {"events"} and Recent["events"][0]["id"] == Through
    _ = Client.RunCli("resource", "operator:available", "--available")
    EventIds = [RowInfo["id"] for RowInfo in PageInfo["events"]]
    while PageInfo["next_after"] is not None:
        Cursor = PageInfo["next_after"]
        PageInfo = JsonCodec.loads(
            Client.RunCli("events", "--after", str(Cursor), "--through", str(Through))
        )
        assert PageInfo["after"] == Cursor and PageInfo["through"] == Through
        assert PageInfo["next_after"] is None or PageInfo["next_after"] > Cursor
        EventIds.extend(RowInfo["id"] for RowInfo in PageInfo["events"])
    assert EventIds == list(range(1, Through + 1))
    Following = JsonCodec.loads(Client.RunCli("events", "--after", str(Through)))
    assert Following["events"][0]["id"] == Through + 1
    assert Following["events"][0]["action"] == "resource"


# event reads must honor supervised ownership while leaving the durable store byte identical
def CheckEventOwner(TmpPath: FilePath) -> None:
    Client = JobClient(TmpPath)
    OwnerToken = "a" * 64
    _ = Client.RunCli("rotate-owner", "--new-owner", OwnerToken)
    Database = TmpPath / "State" / "ledger.sqlite3"
    Before = Database.read_bytes()
    _ = Client.RunCli("--owner", "b" * 64, "events", "--after", "0", ExitCode=5)
    Result = JsonCodec.loads(
        Client.RunCli("--owner", OwnerToken, "events", "--after", "0")
    )
    assert [RowInfo["action"] for RowInfo in Result["events"]] == [
        "supervisor_owner_rotated"
    ]
    _ = Client.RunCli("events", "--after", "-1", ExitCode=1)
    _ = Client.RunCli("events", "--after", "0", "--through", "2", ExitCode=1)
    _ = Client.RunCli("events", "--after", "9223372036854775808", ExitCode=1)
    assert Database.read_bytes() == Before
