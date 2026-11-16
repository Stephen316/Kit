from dataclasses import dataclass as MakeDataClass


# body recipe needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class BodyRecipe:
    PrimaryTagIndex: int
    LwdTagIndex: int
