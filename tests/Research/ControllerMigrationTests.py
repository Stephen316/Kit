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
        assert JsonCodec.loads(Client.RunCli("init"))["store_version"] == 4
        with Closing(Sqlite.connect(RootPath / "State/ledger.sqlite3")) as SchemaDb:
            _ = SchemaDb.execute(
                "DELETE FROM settings WHERE key IN ('job_count','definition_bytes')"
            )
            _ = SchemaDb.execute("PRAGMA user_version=2")
            SchemaDb.commit()
        assert JsonCodec.loads(Client.RunCli("init"))["store_version"] == 4
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "migrated:pending",
                    "kind": "fixture.inspect",
                    "inputs": {},
                    "rule_version": "rule@1",
                    "tool_version": "tool@1",
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit", str(JobFile))
        _ = Client.RunCli("resource", "provider:migrated", "--available")
        with Closing(Sqlite.connect(RootPath / "State/ledger.sqlite3")) as SchemaDb:
            _ = SchemaDb.execute("DROP INDEX jobs_pool_claim")
            _ = SchemaDb.execute("DROP INDEX pool_members")
            _ = SchemaDb.execute("DROP TABLE pool_kinds")
            _ = SchemaDb.execute("ALTER TABLE jobs DROP COLUMN kind")
            _ = SchemaDb.execute("ALTER TABLE resources DROP COLUMN capacity")
            _ = SchemaDb.execute("PRAGMA user_version=3")
            SchemaDb.commit()
        _ = Client.RunCli("pool", "inspect", "--kind", "fixture.inspect")
        with Closing(Sqlite.connect(RootPath / "State/ledger.sqlite3")) as SchemaDb:
            assert SchemaDb.execute("PRAGMA user_version").fetchone()[0] == 4
            assert SchemaDb.execute(
                "SELECT capacity FROM resources WHERE name='provider:migrated'"
            ).fetchone() == (1,)
        PendingFile = RootPath / "Pending.json"
        Claimed = JsonCodec.loads(
            Client.RunCli(
                "claim",
                "--worker",
                "worker:migration",
                "--pool",
                "inspect",
                "--claim-file",
                str(PendingFile),
            )
        )
        assert Claimed["job"] == "migrated:pending"
        Migrated = JsonCodec.loads(Client.RunCli("status", "--job", "migrated"))
        assert Migrated["jobs"][0]["state"] == "completed"
        assert Migrated["jobs"][0]["kind"] == "fixture.inspect"
        with Closing(Sqlite.connect(RootPath / "State/ledger.sqlite3")) as SchemaDb:
            _ = SchemaDb.execute("PRAGMA user_version=5")
            SchemaDb.commit()
        _ = Client.RunCli("status", ExitCode=1)
