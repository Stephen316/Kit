from dataclasses import dataclass as MakeDataClass


# store block needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class StoreBlock:
    NextIndex: int
    IsRoot: bool
    Payload: bytes
