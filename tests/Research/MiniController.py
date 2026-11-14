import contextlib as Contexts
import dataclasses as Dataclasses
import fcntl as FileLocks
import hashlib as Hashing
import json as JsonCodec
import os as OsLayer
import secrets as Secrets
import shutil as Shutil
import time as TimeClock
from collections.abc import Generator
from pathlib import Path as FilePath


@Dataclasses.dataclass
class JobEntry:
    RawSpec: dict[str, object]
    KindName: str
    Inputs: dict[str, str]
    Depends: list[str]
    Resources: list[str]
    MaxAttempts: int
    LeaseSeconds: int
    TimeoutSeconds: int
    JobState: str = "queued"
    Attempts: int = 0
    Generation: int = 0
    PrintHash: str = ""
    ClaimHash: str = ""
    TokenHash: str = ""
    LeaseUntil: float = 0.0
    Deadline: float = 0.0
    ResultHash: str = ""
    Reason: str = ""
    Order: int = 0


@Dataclasses.dataclass
class StoreState:
    JobMap: dict[str, JobEntry]
    Bindings: dict[str, str]
    Pools: dict[str, str]
    Capacity: dict[str, int]
    Counter: int


def HashText(Value: object) -> str:
    return Hashing.sha256(
        JsonCodec.dumps(Value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class JobLifecycle:
    def HashPrereqs(self, Current: StoreState, Entry: JobEntry) -> str:
        DepResults = {
            ItemName: (
                Current.JobMap[ItemName].ResultHash
                if ItemName in Current.JobMap
                and Current.JobMap[ItemName].JobState == "completed"
                else None
            )
            for ItemName in Entry.Depends
        }
        return HashText(
            {
                "spec": Entry.RawSpec,
                "inputs": {
                    RoleName: Current.Bindings.get(ItemName)
                    for RoleName, ItemName in Entry.Inputs.items()
                },
                "dependencies": DepResults,
            }
        )

    def SettleJobs(self, Current: StoreState) -> None:
        Changed = True
        while Changed:
            Changed = False
            for Entry in Current.JobMap.values():
                PrintHash = self.HashPrereqs(Current, Entry)
                if Entry.PrintHash != PrintHash:
                    Entry.PrintHash = PrintHash
                    Entry.Generation += 1
                    Entry.Attempts = 0
                    Entry.JobState = "queued"
                    Entry.TokenHash = ""
                    Entry.ResultHash = ""
                    Entry.Reason = "prerequisites changed"
                    Changed = True
                Expired = min(Entry.LeaseUntil, Entry.Deadline) <= TimeClock.time()
                if Entry.JobState == "running" and Expired:
                    Entry.TokenHash = ""
                    Exhausted = Entry.Attempts >= Entry.MaxAttempts
                    Entry.JobState = "failed" if Exhausted else "queued"
                    Entry.Reason = "lease or execution deadline expired"


class MiniState(JobLifecycle):
    def __init__(self, Options: dict[str, object]) -> None:
        super().__init__()
        self.RootPath = FilePath(str(Options["root"])).resolve()
        (self.RootPath / "objects").mkdir(parents=True, exist_ok=True, mode=0o700)

    def LockPath(self) -> FilePath:
        return self.RootPath / "supervisor.lock"

    @Contexts.contextmanager
    def OpenState(self) -> Generator[StoreState]:
        Handle = OsLayer.open(
            self.RootPath / "state.lock", OsLayer.O_CREAT | OsLayer.O_RDWR, 0o600
        )
        try:
            FileLocks.flock(Handle, FileLocks.LOCK_EX)
            StatePath = self.RootPath / "state.json"
            if StatePath.is_file():
                RawState = JsonCodec.loads(StatePath.read_text(encoding="utf-8"))
                Current = StoreState(
                    JobMap={
                        ItemName: JobEntry(**Entry)
                        for ItemName, Entry in RawState["JobMap"].items()
                    },
                    Bindings=RawState["Bindings"],
                    Pools=RawState["Pools"],
                    Capacity=RawState["Capacity"],
                    Counter=RawState["Counter"],
                )
            else:
                Current = StoreState({}, {}, {}, {}, 0)
            self.SettleJobs(Current)
            yield Current
            self.SettleJobs(Current)
            StagePath = self.RootPath / f".state-{Secrets.token_hex(8)}"
            _ = StagePath.write_text(
                JsonCodec.dumps(Dataclasses.asdict(Current)), encoding="utf-8"
            )
            OsLayer.replace(StagePath, StatePath)
        finally:
            OsLayer.close(Handle)


class MiniObjects(MiniState):
    def StoreBytes(self, Content: bytes) -> str:
        Digest = Hashing.sha256(Content).hexdigest()
        TargetPath = self.RootPath / "objects" / Digest
        if not TargetPath.exists():
            StagePath = self.RootPath / "objects" / f".{Secrets.token_hex(8)}"
            _ = StagePath.write_bytes(Content)
            OsLayer.replace(StagePath, TargetPath)
        return Digest

    def BindInput(self, BindName: str, InputPath: FilePath) -> dict[str, object]:
        Digest = self.StoreBytes(FilePath(InputPath).read_bytes())
        with self.OpenState() as Current:
            Current.Bindings[BindName] = Digest
        return {"name": BindName, "sha256": Digest}

    def FetchInput(self, Digest: str, TargetPath: FilePath) -> int:
        SourcePath = self.RootPath / "objects" / Digest
        Content = SourcePath.read_bytes()
        if Hashing.sha256(Content).hexdigest() != Digest:
            raise ValueError("input object does not match its digest")
        with SourcePath.open("rb") as Source, open(TargetPath, "xb") as Output:
            Shutil.copyfileobj(Source, Output)
        return len(Content)


class MiniResources(MiniState):
    def DefinePool(self, PoolName: str, KindList: list[str]) -> dict[str, object]:
        with self.OpenState() as Current:
            for KindName in KindList:
                if Current.Pools.get(KindName, PoolName) != PoolName:
                    raise ValueError("job kind already belongs to another pool")
            for KindName in [
                KindKey
                for KindKey, PoolKey in Current.Pools.items()
                if PoolKey == PoolName
            ]:
                del Current.Pools[KindName]
            Current.Pools.update({KindName: PoolName for KindName in KindList})
        return {"pool": PoolName, "kinds": sorted(KindList)}

    def DefineResource(self, ResName: str, Capacity: int) -> dict[str, object]:
        with self.OpenState() as Current:
            Current.Capacity[ResName] = Capacity
        return {"name": ResName, "capacity": Capacity}


class MiniQueue(MiniState):
    def SubmitJobs(self, BatchPath: FilePath) -> dict[str, object]:
        RawBatch = JsonCodec.loads(FilePath(BatchPath).read_text(encoding="utf-8"))
        with self.OpenState() as Current:
            for RawSpec in RawBatch["jobs"]:
                Entry = JobEntry(
                    RawSpec=RawSpec,
                    KindName=str(RawSpec["kind"]),
                    Inputs={
                        str(RoleName): str(ItemName)
                        for RoleName, ItemName in RawSpec["inputs"].items()
                    },
                    Depends=[
                        str(ItemName) for ItemName in RawSpec.get("depends_on", [])
                    ],
                    Resources=[
                        str(ItemName) for ItemName in RawSpec.get("resources", [])
                    ],
                    MaxAttempts=int(RawSpec.get("max_attempts", 3)),
                    LeaseSeconds=int(RawSpec.get("lease_seconds", 60)),
                    TimeoutSeconds=int(RawSpec.get("timeout_seconds", 300)),
                )
                Previous = Current.JobMap.get(str(RawSpec["id"]))
                if Previous is not None and Previous.RawSpec == Entry.RawSpec:
                    continue
                Current.Counter += 1
                Entry.Order = Current.Counter
                Current.JobMap[str(RawSpec["id"])] = Entry
            return {"submitted": len(RawBatch["jobs"])}

    def ReadStatus(
        self, JobName: str | None = None, After: str | None = None
    ) -> dict[str, object]:
        with self.OpenState() as Current:
            Names = sorted(
                ItemName
                for ItemName in Current.JobMap
                if (JobName is None or ItemName == JobName)
                and (After is None or ItemName > After)
            )
            return {
                "jobs": [
                    {
                        "id": ItemName,
                        "kind": Current.JobMap[ItemName].KindName,
                        "state": Current.JobMap[ItemName].JobState,
                        "generation": Current.JobMap[ItemName].Generation,
                        "attempts": Current.JobMap[ItemName].Attempts,
                        "result": Current.JobMap[ItemName].ResultHash or None,
                        "reason": Current.JobMap[ItemName].Reason,
                    }
                    for ItemName in Names
                ],
                "next_after": None,
            }


def IsJobReady(
    Entry: JobEntry, Current: StoreState, PoolName: str, Running: list[JobEntry]
) -> bool:
    return (
        Entry.JobState == "queued"
        and Current.Pools.get(Entry.KindName) == PoolName
        and all(ItemName in Current.Bindings for ItemName in Entry.Inputs.values())
        and all(
            ItemName in Current.JobMap
            and Current.JobMap[ItemName].JobState == "completed"
            for ItemName in Entry.Depends
        )
        and all(
            sum(ItemName in Other.Resources for Other in Running)
            < Current.Capacity.get(ItemName, 0)
            for ItemName in Entry.Resources
        )
    )


def BuildClaim(
    JobName: str, Entry: JobEntry, Current: StoreState
) -> dict[str, object]:
    return {
        "job": dict(
            Entry.RawSpec,
            depends_on=Entry.Depends,
            resources=Entry.Resources,
            options=Entry.RawSpec.get("options", {}),
            lease_seconds=Entry.LeaseSeconds,
            timeout_seconds=Entry.TimeoutSeconds,
            max_attempts=Entry.MaxAttempts,
        ),
        "generation": Entry.Generation,
        "attempt": Entry.Attempts,
        "fingerprint": Entry.PrintHash,
        "snapshot": {
            "inputs": {
                RoleName: {
                    "binding": ItemName,
                    "sha256": Current.Bindings[ItemName],
                }
                for RoleName, ItemName in Entry.Inputs.items()
            },
            "dependencies": {
                ItemName: {"result": Current.JobMap[ItemName].ResultHash}
                for ItemName in Entry.Depends
            },
        },
        "lease_until": Entry.LeaseUntil,
        "deadline": Entry.Deadline,
        "job_id": JobName,
    }


def StartLeaseMut(Entry: JobEntry, Worker: str, Token: str) -> None:
    Started = TimeClock.time()
    Entry.Attempts += 1
    Entry.JobState = "running"
    Entry.TokenHash = Hashing.sha256(Token.encode()).hexdigest()
    Entry.ClaimHash = Entry.PrintHash
    Entry.Deadline = Started + Entry.TimeoutSeconds
    Entry.LeaseUntil = min(Entry.Deadline, Started + Entry.LeaseSeconds)
    Entry.Reason = f"claimed by {Worker}"


def WriteClaim(
    ClaimPath: FilePath, ClaimInfo: dict[str, object], Token: str
) -> None:
    Handle = OsLayer.open(
        ClaimPath, OsLayer.O_CREAT | OsLayer.O_EXCL | OsLayer.O_WRONLY, 0o600
    )
    with OsLayer.fdopen(Handle, "w", encoding="utf-8") as Output:
        _ = Output.write(JsonCodec.dumps(dict(ClaimInfo, lease_token=Token)))


class MiniClaims(MiniState):
    def ClaimJob(
        self, PoolName: str, Worker: str, ClaimPath: FilePath
    ) -> dict[str, object] | None:
        with self.OpenState() as Current:
            if PoolName not in Current.Pools.values():
                raise ValueError("pool has no registered job kinds")
            Running = [
                Entry
                for Entry in Current.JobMap.values()
                if Entry.JobState == "running"
            ]
            for JobName, Entry in sorted(
                Current.JobMap.items(), key=lambda JobPair: JobPair[1].Order
            ):
                if not IsJobReady(Entry, Current, PoolName, Running):
                    continue
                if Entry.Attempts >= Entry.MaxAttempts:
                    Entry.JobState = "failed"
                    continue
                Token = Secrets.token_hex(32)
                StartLeaseMut(Entry, Worker, Token)
                ClaimInfo = BuildClaim(JobName, Entry, Current)
                WriteClaim(ClaimPath, ClaimInfo, Token)
                return ClaimInfo
        return None


class MiniLeases(MiniObjects):
    def CheckLease(self, Current: StoreState, ClaimPath: FilePath) -> JobEntry | None:
        ClaimInfo = JsonCodec.loads(FilePath(ClaimPath).read_text(encoding="utf-8"))
        Entry = Current.JobMap.get(str(ClaimInfo["job_id"]))
        TokenHash = Hashing.sha256(str(ClaimInfo["lease_token"]).encode()).hexdigest()
        if (
            Entry is None
            or Entry.JobState != "running"
            or Entry.TokenHash != TokenHash
            or Entry.ClaimHash != Entry.PrintHash
            or min(Entry.LeaseUntil, Entry.Deadline) <= TimeClock.time()
        ):
            return None
        return Entry

    def RenewLease(self, ClaimPath: FilePath) -> dict[str, object]:
        with self.OpenState() as Current:
            Entry = self.CheckLease(Current, ClaimPath)
            if Entry is None:
                return {"stale": True}
            Entry.LeaseUntil = min(
                TimeClock.time() + Entry.LeaseSeconds, Entry.Deadline
            )
            return {
                "stale": False,
                "lease_until": Entry.LeaseUntil,
                "deadline": Entry.Deadline,
            }

    def FinishJob(
        self, ClaimPath: FilePath, Outcome: str, ResultPath: FilePath, Reason: str
    ) -> dict[str, object]:
        Digest = self.StoreBytes(FilePath(ResultPath).read_bytes())
        with self.OpenState() as Current:
            Entry = self.CheckLease(Current, ClaimPath)
            if Entry is None:
                return {"stale": True}
            Exhausted = Entry.Attempts >= Entry.MaxAttempts
            Entry.JobState = Outcome
            if Outcome == "retry":
                Entry.JobState = "failed" if Exhausted else "queued"
            Entry.TokenHash = ""
            Entry.ResultHash = Digest
            Entry.Reason = Reason
            return {"stale": False}


class MiniController(MiniResources, MiniQueue, MiniClaims, MiniLeases):
    pass
