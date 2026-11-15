from dataclasses import dataclass as MakeDataClass


# subtype reference needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class SubtypeRef:
    Family: str
    Index: int
