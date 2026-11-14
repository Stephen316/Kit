from dataclasses import dataclass as Dataclass


# numeric fields retain native offsets and units until the neutral projection
@Dataclass(frozen=True, slots=True)
class NativeParam:
    RoleName: str
    ParamName: str
    DisplayUnit: str
    Number: float
    Formula: str
    Comment: str
    BindingId: int | None
    NativeIndex: int
    Metadata: bytes
    CollectionId: int
