import json as JsonCodec
from pathlib import Path as FilePath

from tests.Research.MiniAdapter.JobEntry import JobEntry
from tests.Research.MiniAdapter.MiniState import MiniState


# supervisor coverage needs queue setup and status without depending on the production store
class MiniQueue(MiniState):

    # submitted jobs must survive controller process calls and retain their original ordering
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

    # callers need stable status pages to verify completion across controller process boundaries
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
