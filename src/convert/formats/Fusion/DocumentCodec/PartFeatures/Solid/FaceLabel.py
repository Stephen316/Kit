from dataclasses import dataclass as MakeDataClass


# face label needs an explicit state contract so body topology remains consistent with its modeling operation
@MakeDataClass(frozen=True, slots=True)
class FaceLabel:
    PrimaryId: str
    OperationIds: tuple[int, ...]
    SecondaryId: int = 0
    Merged: tuple["FaceLabel", ...] = ()
