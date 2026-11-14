import json as JsonCodec
import sqlite3 as Sqlite
import tempfile as TempFiles
from contextlib import closing as Closing
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def SubmitMigration(Client: JobClient, JobFile: FilePath, JobName: str) -> None:
    _ = JobFile.write_text(
        JsonCodec.dumps(
            {
                "id": JobName,
                "kind": "fixture.inspect",
                "inputs": {},
                "rule_version": "rule@1",
                "tool_version": "tool@1",
            }
        ),
        encoding="utf-8",
    )
    _ = Client.RunCli("submit", str(JobFile))


def DowngradeStore(Database: FilePath, Version: int, *Statements: str) -> None:
    with Closing(Sqlite.connect(Database)) as SchemaDb:
        for Statement in Statements:
            _ = SchemaDb.execute(Statement)
        _ = SchemaDb.execute(f"PRAGMA user_version={Version}")
        SchemaDb.commit()


def FinishMigration(Client: JobClient, RootPath: FilePath, JobFile: FilePath) -> None:
    SubmitMigration(Client, JobFile, "migrated")
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


def AssertEarlyDb(Client: JobClient, Database: FilePath) -> None:
    CountsSql = "DELETE FROM settings WHERE key IN ('job_count','definition_bytes')"
    DowngradeStore(
        Database,
        1,
        "DROP TABLE dirty",
        "DROP TABLE job_inputs",
        "DROP TABLE job_resources",
        "DROP INDEX jobs_claim",
        "DROP INDEX jobs_leases",
        CountsSql,
    )
    assert (
        JsonCodec.loads(Client.RunCli("status", "--job", "migrated"))["jobs"][0][
            "state"
        ]
        == "completed"
    )
    assert JsonCodec.loads(Client.RunCli("init"))["store_version"] == 4
    DowngradeStore(Database, 2, CountsSql)
    assert JsonCodec.loads(Client.RunCli("init"))["store_version"] == 4


def AssertPoolStore(Client: JobClient, RootPath: FilePath, Database: FilePath) -> None:
    _ = Client.RunCli("resource", "provider:migrated", "--available")
    DowngradeStore(
        Database,
        3,
        "DROP INDEX jobs_pool_claim",
        "DROP INDEX pool_members",
        "DROP TABLE pool_kinds",
        "ALTER TABLE jobs DROP COLUMN kind",
        "ALTER TABLE resources DROP COLUMN capacity",
    )
    _ = Client.RunCli("pool", "inspect", "--kind", "fixture.inspect")
    with Closing(Sqlite.connect(Database)) as SchemaDb:
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


def CheckStoreMove() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath)
        JobFile = RootPath / "Job.json"
        Database = RootPath / "State/ledger.sqlite3"
        FinishMigration(Client, RootPath, JobFile)
        AssertEarlyDb(Client, Database)
        SubmitMigration(Client, JobFile, "migrated:pending")
        AssertPoolStore(Client, RootPath, Database)
        DowngradeStore(Database, 5)
        _ = Client.RunCli("status", ExitCode=1)
