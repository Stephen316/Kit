import hashlib as Hashing
import time as TimeClock

from tests.Research.MiniAdapter.JobEntry import JobEntry


def StartLeaseMut(Entry: JobEntry, Worker: str, Token: str) -> None:
    Started = TimeClock.time()
    Entry.Attempts += 1
    Entry.JobState = "running"
    Entry.TokenHash = Hashing.sha256(Token.encode()).hexdigest()
    Entry.ClaimHash = Entry.PrintHash
    Entry.Deadline = Started + Entry.TimeoutSeconds
    Entry.LeaseUntil = min(Entry.Deadline, Started + Entry.LeaseSeconds)
    Entry.Reason = f"claimed by {Worker}"
