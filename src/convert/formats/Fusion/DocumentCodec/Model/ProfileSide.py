from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ProfileSide:
    ProgenitorRole: str
    RecipeRole: str
    ProgenitorTag: int
    SketchTag: int
    PreviousTag: int | None = None
    FollowingTag: int | None = None
