# the pole count contract needs a shared interpretation so nested spline and surface records retain their relationships
def PoleCount(Degree: int, Multiplicity: tuple[int, ...]) -> int:
    return sum(Multiplicity) - Degree + 1
