from dataclasses import dataclass as Dataclass


# raw occurrence ownership is verified before replacing collections with component ids
@Dataclass(frozen=True, slots=True)
class OccurRecord:
    ObjectId: int
    ComponentId: int
    CollectionId: int | None
    Name: str
    InstanceNumber: int
    NativeGuid: str
    Transform: tuple[float, ...]
