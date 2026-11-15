from dataclasses import dataclass as MakeDataClass


# stream state needs an explicit state contract so topology changes retain their native revision relationships
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
