import json as JsonCodec
import sqlite3 as Sqlite
import tempfile as TempFiles
from contextlib import closing as Closing
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def CheckStoreMove() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath)
        JobFile = RootPath / "Job.json"
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "migrated",
                    "kind": "fixture.inspect",
                    "inputs": {},
                    "rule_version": "rule@1",
                    "tool_version": "tool@1",
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit", str(JobFile))
        LeaseFile = RootPath / "Lease.json"
        _ = Client.RunCli(
            "claim", "--worker", "worker:migration", "--claim-file", str(LeaseFile)
        )
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(LeaseFile),
            "--result",
            str(JobFile),
            "--outcome",
            "completed",
            "--reason",
            "fixture complete",
        )
        with Closing(Sqlite.connect(RootPath / "State/ledger.sqlite3")) as SchemaDb:
            _ = SchemaDb.execute("DROP TABLE dirty")
            _ = SchemaDb.execute("DROP TABLE job_inputs")
            _ = SchemaDb.execute("DROP TABLE job_resources")
            _ = SchemaDb.execute("DROP INDEX jobs_claim")
            _ = SchemaDb.execute("DROP INDEX jobs_leases")
            _ = SchemaDb.execute(
                "DELETE FROM settings WHERE key IN ('job_count','definition_bytes')"
            )
            _ = SchemaDb.execute("PRAGMA user_version=1")
            SchemaDb.commit()
        assert (
            JsonCodec.loads(Client.RunCli("status", "--job", "migrated"))["jobs"][0][
                "state"
            ]
            == "completed"
        )
        assert JsonCodec.loads(Client.RunCli("init"))["store_version"] == 3
        with Closing(Sqlite.connect(RootPath / "State/ledger.sqlite3")) as SchemaDb:
            _ = SchemaDb.execute(
                "DELETE FROM settings WHERE key IN ('job_count','definition_bytes')"
            )
            _ = SchemaDb.execute("PRAGMA user_version=2")
            SchemaDb.commit()
        assert JsonCodec.loads(Client.RunCli("init"))["store_version"] == 3
        with Closing(Sqlite.connect(RootPath / "State/ledger.sqlite3")) as SchemaDb:
            _ = SchemaDb.execute("PRAGMA user_version=4")
            SchemaDb.commit()
        _ = Client.RunCli("status", ExitCode=1)
