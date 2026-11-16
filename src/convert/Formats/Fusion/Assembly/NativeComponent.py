from dataclasses import dataclass as Dataclass


# component identity stays separate from each use in the assembly
@Dataclass(frozen=True, slots=True)
class NativeComponent:
    ObjectId: int
    Name: str
    NativeGuid: str
