from dataclasses import dataclass as MakeDataClass


# profile side needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(frozen=True, slots=True)
class ProfileSide:
    ProgenitorRole: str
    RecipeRole: str
    ProgenitorTag: int
    SketchTag: int
    PreviousTag: int | None = None
    FollowingTag: int | None = None
