def PoleCount(Degree: int, Multiplicity: tuple[int, ...]) -> int:
    return sum(Multiplicity) - Degree + 1
