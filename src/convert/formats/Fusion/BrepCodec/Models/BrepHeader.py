from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class BrepHeader:
    FileVersion: int
    RootCount: int
    Flags: int
    Scale: float
    AbsoluteTolerance: float
    NormalTolerance: float
    IntWidth: int = 8
