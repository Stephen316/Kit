import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def CheckAppendJobs() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath)
        JobFile = RootPath / "Job.json"
        for Index in range(300):
            _ = JobFile.write_text(
                JsonCodec.dumps(
                    {
                        "id": f"append:{Index:04d}",
                        "kind": "fixture.inspect",
                        "inputs": {},
                        "depends_on": [f"append:{Index-1:04d}"] if Index else [],
                        "rule_version": "rule@1",
                        "tool_version": "tool@1",
                    }
                ),
                encoding="utf-8",
            )
            Submitted = JsonCodec.loads(Client.RunCli("submit", str(JobFile)))
            assert Submitted["cycle_searches"] == 0
            assert Submitted["reconciled_jobs"] == 1
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "append:0000",
                    "kind": "fixture.inspect",
                    "inputs": {},
                    "depends_on": ["append:0299"],
                    "rule_version": "rule@2",
                    "tool_version": "tool@1",
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit", str(JobFile), ExitCode=1)
        assert (
            JsonCodec.loads(Client.RunCli("status", "--job", "append:0000"))["jobs"][0][
                "state"
            ]
            == "queued"
        )
        assert (
            JsonCodec.loads(Client.RunCli("status", "--job", "append:0299"))["jobs"][0][
                "state"
            ]
            == "waiting_evidence"
        )
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "jobs": [
                        {
                            "id": "append:0000",
                            "kind": "fixture.inspect",
                            "inputs": {},
                            "depends_on": ["append:0001"],
                            "rule_version": "rule@3",
                            "tool_version": "tool@1",
                        },
                        {
                            "id": "append:0001",
                            "kind": "fixture.inspect",
                            "inputs": {},
                            "depends_on": [],
                            "rule_version": "rule@3",
                            "tool_version": "tool@1",
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit-batch", str(JobFile))
        assert (
            JsonCodec.loads(Client.RunCli("status", "--job", "append:0000"))["jobs"][0][
                "state"
            ]
            == "waiting_evidence"
        )
        assert (
            JsonCodec.loads(Client.RunCli("status", "--job", "append:0001"))["jobs"][0][
                "state"
            ]
            == "queued"
        )
