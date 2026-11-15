from dataclasses import dataclass as MakeDataClass


# title text needs an explicit state contract so drawing objects retain valid ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class TitleText:
    Tag: str
    TextValue: str
    WidthFactor: float = 1.0
