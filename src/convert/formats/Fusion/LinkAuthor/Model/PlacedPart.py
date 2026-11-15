from dataclasses import dataclass as MakeDataClass


# placed part needs an explicit state contract so cross document references retain their intended ownership
@MakeDataClass(frozen=True, slots=True)
class PlacedPart:
    TargetIndex: int
    Matrix: tuple[float, ...]
    Grounded: bool = False
