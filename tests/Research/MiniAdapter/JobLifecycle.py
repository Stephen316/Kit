import time as TimeClock

from tests.Research.MiniAdapter.HashText import HashText
from tests.Research.MiniAdapter.JobEntry import JobEntry
from tests.Research.MiniAdapter.StoreState import StoreState


# the adapter needs consistent prerequisite evidence before either claim or completion can settle dependencies
class JobLifecycle:

    # a lease must be bound to the exact prerequisite results it was granted against
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

    # queued fixture jobs must reflect changed prerequisite outcomes before the next claim or status read
    def SettleJobsMut(self, Current: StoreState) -> None:
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
