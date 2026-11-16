from dataclasses import dataclass as MakeDataClass


# boundary representation header needs an explicit state contract so topology identity survives native history reconstruction
@MakeDataClass(frozen=True, slots=True)
class BrepHeader:
    FileVersion: int
    RootCount: int
    Flags: int
    Scale: float
    AbsoluteTolerance: float
    NormalTolerance: float
    IntWidth: int = 8
