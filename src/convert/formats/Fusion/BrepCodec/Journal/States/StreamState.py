from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class StreamState:
    CurrentStateId: int
    MaxStateId: int
    MaxStatesToKeep: int
    NextEntityTag: int
    WorkingNode: int
    ActiveNode: int
    InitialNode: int
    OwnerEntity: int
