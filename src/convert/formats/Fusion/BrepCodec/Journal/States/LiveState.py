from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class LiveState:
    StateId: int
    Versions: tuple[tuple[int, int], ...]
