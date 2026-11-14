from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DirectionValue:
    FieldKey: str
    Direction: str
    Value: float
