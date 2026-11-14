from tests.Research.MiniAdapter.JobEntry import JobEntry
from tests.Research.MiniAdapter.StoreState import StoreState


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
