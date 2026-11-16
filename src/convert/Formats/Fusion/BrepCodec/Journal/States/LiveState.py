from dataclasses import dataclass as MakeDataClass


# live state needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class LiveState:
    StateId: int
    Versions: tuple[tuple[int, int], ...]
