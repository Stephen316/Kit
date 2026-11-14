from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class RecipeTag:
    PrimaryId: tuple[int, ...]
    SecondaryId: int
    OperationIds: tuple[int, ...]
    ApproachId: int
