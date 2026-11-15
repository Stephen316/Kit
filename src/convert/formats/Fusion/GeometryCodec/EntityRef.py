from dataclasses import dataclass as MakeDataClass


# entity reference needs an explicit state contract so geometric values retain their native record boundaries
@MakeDataClass(frozen=True, slots=True)
class EntityRef:
    Index: int
