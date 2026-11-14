from dataclasses import dataclass as DataClass

from tests.Research.JobEntry import JobEntry


@DataClass
class StoreState:
    JobMap: dict[str, JobEntry]
    Bindings: dict[str, str]
    Pools: dict[str, str]
    Capacity: dict[str, int]
    Counter: int
