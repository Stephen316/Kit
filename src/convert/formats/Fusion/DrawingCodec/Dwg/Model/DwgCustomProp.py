from dataclasses import dataclass as MakeDataClass


# drawing custom prop needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgCustomProp:
    PropName: str
    PropValue: str
