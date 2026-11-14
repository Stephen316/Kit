import hashlib as Hashing
import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.MiniAdapter.JobEntry import JobEntry
from tests.Research.MiniAdapter.MiniObjects import MiniObjects
from tests.Research.MiniAdapter.StoreState import StoreState


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
