from dataclasses import dataclass as MakeDataClass


# recipe tag needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class RecipeTag:
    PrimaryId: tuple[int, ...]
    SecondaryId: int
    OperationIds: tuple[int, ...]
    ApproachId: int
