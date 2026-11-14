from tests.Research.JobEntry import JobEntry
from tests.Research.StoreState import StoreState


def BuildClaim(JobName: str, Entry: JobEntry, Current: StoreState) -> dict[str, object]:
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
