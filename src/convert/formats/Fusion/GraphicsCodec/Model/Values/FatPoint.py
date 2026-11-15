from dataclasses import dataclass as MakeDataClass


# fat point needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class FatPoint:
    Width: int
    Height: int
    BoxSize: tuple[float, ...]
