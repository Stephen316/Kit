import hashlib as HashContent
import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient
from tests.Research.SupervisorClient import FixtureJob, KRepoRoot


# a fixed roster must identify live parked controller attempts without changing the store
def CheckBatch(TmpPath: FilePath) -> None:
    Client = JobClient(TmpPath)
    FirstName, NextName = "candidate:first", "candidate:next"
    _ = StageWaiting(Client, TmpPath, FirstName)
    PendingPath = StageWaiting(Client, TmpPath, NextName)
    Revision = CheckoutHead()
    Report = ReadRoster(TmpPath, Revision, (NextName, FirstName))
    assert ReadRoster(TmpPath, Revision, (FirstName, NextName)) == Report
    VerifyRoster(Client, Report, Revision, (FirstName, NextName))
    _ = ReadRoster(TmpPath, Revision, (FirstName, FirstName), ExitCode=1)
    _ = PendingPath.write_bytes(b'{"ci":"changed"}')
    _ = Client.RunCli("bind", f"ci:{NextName}", str(PendingPath))
    _ = ReadRoster(TmpPath, Revision, (FirstName, NextName), ExitCode=1)
    Remaining = ReadRoster(TmpPath, Revision, (FirstName,))
    assert (
        JsonCodec.loads(JsonCodec.dumps(Remaining["members"]))
        == JsonCodec.loads(JsonCodec.dumps(Report["members"]))[:1]
    )
    VerifyCorrupt(TmpPath, Revision, FirstName, Remaining)


# candidates must use real controller settlement and a declared pending input binding
def StageWaiting(Client: JobClient, RootPath: FilePath, JobName: str) -> FilePath:
    Binding = f"ci:{JobName}"
    PendingPath = RootPath / "Pending.json"
    _ = PendingPath.write_bytes(b'{"ci":"pending"}')
    _ = Client.RunCli("bind", Binding, str(PendingPath))
    Definition = RootPath / "Definitions.json"
    JobInfo = FixtureJob(
        JobName, "fixture.verify", inputs={"ci": Binding}, lease_seconds=30
    )
    _ = Definition.write_text(JsonCodec.dumps(JobInfo), encoding="utf-8")
    _ = Client.RunCli("submit", str(Definition))
    LeasePath = RootPath / f"Waiting-{JobName.removeprefix('candidate:')}.json"
    _ = Client.RunCli(
        "claim", "--worker", "fixture:verification", "--claim-file", str(LeasePath)
    )
    _ = Client.RunCli(
        "finish",
        "--lease",
        str(LeasePath),
        "--result",
        str(PendingPath),
        "--outcome",
        "waiting_ci",
        "--reason",
        "fixture pending remote verification",
    )
    return PendingPath


# the batch revision must identify the actual checkout used by the hosted candidate
def CheckoutHead() -> str:
    Response = Subprocess.run(
        ["git", "-C", str(KRepoRoot), "rev-parse", "--verify", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    return Response.stdout.strip()


# a read only invocation must preserve controller ledger bytes on success and refusal
def ReadRoster(
    RootPath: FilePath, Revision: str, Names: tuple[str, ...], ExitCode: int = 0
) -> dict[str, object]:
    StorePath = RootPath / "State"
    LedgerPath = StorePath / "ledger.sqlite3"
    Before = LedgerPath.read_bytes()
    Program = KRepoRoot / "re/automation/CiBatch.py"
    Arguments = [
        System.executable,
        str(Program),
        "--store",
        str(StorePath),
        "--batch-revision",
        Revision,
    ]
    for JobName in Names:
        Arguments.extend(("--job", JobName))
    Response = Subprocess.run(
        Arguments, capture_output=True, text=True, check=False, timeout=35
    )
    assert Response.returncode == ExitCode, Response.stderr
    assert LedgerPath.read_bytes() == Before
    Report: dict[str, object] = (
        JsonCodec.loads(Response.stdout) if ExitCode == 0 else {}
    )
    return Report


# the roster must retain exact controller fingerprints receipts and candidate ordering
def VerifyRoster(
    Client: JobClient, Report: dict[str, object], Revision: str, Names: tuple[str, ...]
) -> None:
    Payload = dict(Report)
    PayloadHash = Payload.pop("payload_sha256")
    Exact = JsonCodec.dumps(
        Payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    assert PayloadHash == HashContent.sha256(Exact.encode("utf-8")).hexdigest()
    assert Report["scope"] == "pending_ci_roster"
    assert Report["batch_revision"] == Revision and Report["ci_role"] == "ci"
    Members = JsonCodec.loads(JsonCodec.dumps(Report["members"]))
    assert tuple(Member["job_id"] for Member in Members) == Names
    for Member in Members:
        Status = JsonCodec.loads(Client.RunCli("status", "--job", Member["job_id"]))[
            "jobs"
        ][0]
        assert Status["state"] == "waiting_ci"
        assert Member["attempt"] == Status["attempts"] == 1
        assert Member["generation"] == Status["generation"]
        assert Member["fingerprint"] == Status["fingerprint"]
        assert Member["waiting_receipt_sha256"] == Status["receipt"]
        assert Member["waiting_result_sha256"] == Status["result"]
        assert (
            Member["ci_input_sha256"]
            == HashContent.sha256(b'{"ci":"pending"}').hexdigest()
        )


# exact receipt custody must fail when its retained bytes differ from the label
def VerifyCorrupt(
    RootPath: FilePath, Revision: str, JobName: str, Roster: dict[str, object]
) -> None:
    Items = JsonCodec.loads(JsonCodec.dumps(Roster["members"]))
    Checksum: str = Items[0]["waiting_receipt_sha256"]
    ReceiptPath = RootPath / "State" / "objects" / Checksum[:2] / Checksum
    Original = ReceiptPath.read_bytes()
    try:
        _ = ReceiptPath.write_bytes(Original + b" ")
        _ = ReadRoster(RootPath, Revision, (JobName,), ExitCode=1)
    finally:
        _ = ReceiptPath.write_bytes(Original)
