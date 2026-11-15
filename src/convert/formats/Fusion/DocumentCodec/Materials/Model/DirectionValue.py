from dataclasses import dataclass as MakeDataClass


# direction value needs an explicit state contract so appearance references remain connected to their owning entities
@MakeDataClass(frozen=True, slots=True)
class DirectionValue:
    FieldKey: str
    Direction: str
    Value: float
