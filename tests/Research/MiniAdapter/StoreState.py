from dataclasses import dataclass as DataClass

from tests.Research.MiniAdapter.JobEntry import JobEntry


# all fixture queue and resource data must round trip together between adapter processes
@DataClass
class StoreState:
    JobMap: dict[str, JobEntry]
    Bindings: dict[str, str]
    Pools: dict[str, str]
    Capacity: dict[str, int]
    Counter: int
