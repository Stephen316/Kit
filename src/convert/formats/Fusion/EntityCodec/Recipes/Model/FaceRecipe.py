from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class FaceRecipe:
    PrimaryTagIndex: int
    LwdTagIndex: int
