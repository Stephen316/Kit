from dataclasses import dataclass as Dataclass


# stored sibling order and placement belong to the occurrence rather than its definition
@Dataclass(frozen=True, slots=True)
class NativeOccur:
    ObjectId: int
    ComponentId: int
    OwnerId: int
    Name: str
    InstanceNumber: int
    NativeGuid: str
    Order: int
    Transform: tuple[float, ...]
