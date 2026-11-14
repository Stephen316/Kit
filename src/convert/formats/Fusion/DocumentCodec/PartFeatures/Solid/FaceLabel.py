from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class FaceLabel:
    PrimaryId: str
    OperationIds: tuple[int, ...]
    SecondaryId: int = 0
    Merged: tuple["FaceLabel", ...] = ()
