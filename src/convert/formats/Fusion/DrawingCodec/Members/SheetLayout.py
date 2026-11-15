from dataclasses import dataclass as MakeDataClass


# sheet layout needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class SheetLayout:
    ActiveSheet: str
    SheetSize: str
    Standard: str
    Units: str
    Width: float
    Height: float
    HorizontalZones: int
    VerticalZones: int
