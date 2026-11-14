from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class StoreBlock:
    NextIndex: int
    IsRoot: bool
    Payload: bytes
